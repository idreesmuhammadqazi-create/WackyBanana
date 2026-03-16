import numpy, soundfile
import os,requests 


ScriptFolder = os.path.dirname(os.path.abspath(__file__))
ImagePath = os.path.join(ScriptFolder, "Banana.png")
# Not Putting JWT here because it needs to be anonymous but if we do it will upload
PinataJWT = ""

SampleRate = 44100
SymbolDuration = 0.05
Frequencies = [1000,1300,1600,1900,2200,2500,2800,3100]
PreambleBytes = [170 for _ in range(40)]
def Encoder():
    def GenerateSymbol(ByteValue):
        NoOfSamples = int(SampleRate * SymbolDuration)
        TimeAxis = numpy.linspace(
            0,SymbolDuration,NoOfSamples,False
        )
        Waveform = numpy.zeros(NoOfSamples)
        for BitIndex in range(8):
            Bit = (ByteValue >> BitIndex) & 1
            if Bit == 1:
                Frequency = Frequencies[BitIndex]
                Waveform += numpy.sin(2*numpy.pi *Frequency *TimeAxis)
        
        FadeSamples = int(SampleRate *0.003)
        Envelope = numpy.ones(NoOfSamples)
        Envelope[:FadeSamples] = numpy.linspace(
            0,1,FadeSamples
        )
        Envelope[-FadeSamples:] = numpy.linspace(
            0,1,FadeSamples
        )
        Waveform *= Envelope
        return Waveform


    #----------------------Main Program------------------------
    with open(ImagePath, "rb") as ImageFile:
        ImageBytes = ImageFile.read()

    ImageSize = len(ImageBytes)
    SizeBytes = ImageSize.to_bytes(4,"big")
    PayLoad = bytes(PreambleBytes) + SizeBytes + ImageBytes
    AudioSegments = []
    for ByteValue in PayLoad:
        SymbolWave = GenerateSymbol(ByteValue)
        AudioSegments.append(SymbolWave)
    AudioWaveform = numpy.concatenate(AudioSegments)
    AudioWaveform = AudioWaveform/ numpy.max(numpy.abs(AudioWaveform))
    soundfile.write(
        "Banana.wav",
        AudioWaveform,SampleRate
    )

    print("We Good")

def Decoder():
    def DetectByte(SymbolSamples):
        Spectrum = numpy.fft.rfft(SymbolSamples)
        FreqAxis = numpy.fft.rfftfreq(len(SymbolSamples), 1 / SampleRate)

        ByteValue = 0
        for BitIndex, Frequency in enumerate(Frequencies):
            BinIndex = numpy.argmin(numpy.abs(FreqAxis - Frequency))
            WindowStart = max(0, BinIndex - 2)
            WindowEnd   = min(len(Spectrum), BinIndex + 3)
            Magnitude = numpy.max(numpy.abs(Spectrum[WindowStart:WindowEnd]))

            if Magnitude > Threshold:
                ByteValue |= (1 << BitIndex)

        return ByteValue

    def CalibateThreshold(AudioWaveform):
        NoOfSamples = int(SampleRate * SymbolDuration)
        FirstSymbol = AudioWaveform[:NoOfSamples]
        Spectrum = numpy.fft.rfft(FirstSymbol)
        FreqAxis = numpy.fft.rfftfreq(NoOfSamples, 1 / SampleRate)

        Magnitudes = []
        for Frequency in Frequencies:
            BinIndex = numpy.argmin(numpy.abs(FreqAxis - Frequency))
            Magnitudes.append(numpy.abs(Spectrum[BinIndex]))

        ActiveMags   = [Magnitudes[i] for i in [1, 3, 5, 7]]
        InactiveMags = [Magnitudes[i] for i in [0, 2, 4, 6]]
        return (min(ActiveMags) + max(InactiveMags)) / 2

    # ---------------------- Main Program ------------------------
    AudioWaveform, SR = soundfile.read("Banana.wav")
    if SR != SampleRate:
        raise ValueError(f"Unexpected sample rate: {SR}, expected {SampleRate}")

    NoOfSamples = int(SampleRate * SymbolDuration)

    Threshold = CalibateThreshold(AudioWaveform)
    print(f"Calibrated threshold: {Threshold:.2f}")

    TotalSamples = len(AudioWaveform)
    DecodedBytes = []
    for Offset in range(0, TotalSamples - NoOfSamples + 1, NoOfSamples):
        SymbolSamples = AudioWaveform[Offset : Offset + NoOfSamples]
        DecodedBytes.append(DetectByte(SymbolSamples))

    PreamblePattern = bytes(PreambleBytes)
    DecodedByteStr  = bytes(DecodedBytes)
    PreambleIndex   = DecodedByteStr.find(PreamblePattern)
    if PreambleIndex == -1:
        raise ValueError("Preamble not found — sync failed")

    PayloadStart = PreambleIndex + len(PreambleBytes)

    SizeBytes    = DecodedByteStr[PayloadStart : PayloadStart + 4]
    ImageSize    = int.from_bytes(SizeBytes, "big")
    print(f"Expected image size: {ImageSize} bytes")

    ImageStart = PayloadStart + 4
    ImageBytes = DecodedByteStr[ImageStart : ImageStart + ImageSize]

    if len(ImageBytes) < ImageSize:
        raise ValueError(f"Incomplete data: got {len(ImageBytes)}/{ImageSize} bytes")

    OutputPath = os.path.join(ScriptFolder, "Banana_Decoded.png")
    with open(OutputPath, "wb") as OutputFile:
        OutputFile.write(ImageBytes)

    print(f"Image recovered → {OutputPath}")

def UploadToPinata(FilePath):
    with open(FilePath, "rb") as AudioFile:
        Response = requests.post(
            "https://api.pinata.cloud/pinning/pinFileToIPFS",
            headers={"Authorization": f"Bearer {PinataJWT}"},
            files={"file": ("Banana.wav", AudioFile, "audio/wav")},
            data={"pinataMetadata": '{"name": "Banana"}'}
        )
    ContentId = Response.json()["IpfsHash"]
    print(f"Stored on IPFS! CID: {ContentId}")
    return ContentId

def DownloadFromIPFS(ContentId, SavePath="Banana.wav"):
    Response = requests.get(
        f"https://gateway.pinata.cloud/ipfs/{ContentId}",
        stream=True
    )
    if Response.status_code != 200:
        raise ValueError(f"Download failed: {Response.status_code}")
    with open(SavePath, "wb") as AudioFile:
        for Chunk in Response.iter_content(chunk_size=8192):
            AudioFile.write(Chunk)
    print(f"Retrieved to {SavePath}")

Choice = input("Do you want to store the banana or retrieve(S or R), anything other than that to exit:")
if Choice.lower() == "s":
    Encoder()
    if PinataJWT != "":
        UploadToPinata()
elif Choice.lower() == "r":
    CID = "bafybeicdbpzmknwo2lvmmqq6wplqxabj7ae43iukftmjzz6kgjjho5lhd4"
    DownloadFromIPFS(CID,)
    Decoder()
else:
    pass

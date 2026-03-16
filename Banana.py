import numpy, soundfile
import os

ScriptFolder = os.path.dirname(os.path.abspath(__file__))
ImagePath = os.path.join(ScriptFolder, "Banana.png")

SampleRate = 44100
SymbolDuration = 0.05
Frequencies = [1000,1300,1600,1900,2200,2500,2800,3100]

PreambleBytes = [170 for _ in range(40)]
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
    BananaAudio,
    AudioWaveform,SampleRate
)

print("We Good")

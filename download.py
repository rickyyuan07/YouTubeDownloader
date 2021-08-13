from pytube import YouTube

def download(url: str):
    yt = YouTube(url)
    yt.streams.filter(only_audio=True).first().download()
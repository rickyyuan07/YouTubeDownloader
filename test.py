from PIL import Image,ImageTk
import tkinter as tk
from tkinter import messagebox
from pytube import YouTube
#-----------------------------------------------------------------
import os
import subprocess
# 引入 requests 模組
import requests as req
# 引入 Beautiful Soup 模組
from bs4 import BeautifulSoup
# 引入 re 模組
import re
#-----------------------------------------------------------------

fileobj = {}
download_count = 1

#--------------------函式區域----------------------------------------------
# 檢查影片檔是否包含聲音
def check_media(filename):
    r = subprocess.Popen(["ffprobe", filename],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = r.communicate()

    if (out.decode('utf-8').find('Audio') == -1):
        return -1  # 沒有聲音
    else:
        return 1

# 合併影片檔
def merge_media():
    temp_video = os.path.join(fileobj['dir'], 'temp_video.mp4')
    temp_audio = os.path.join(fileobj['dir'], 'temp_audio.mp4')
    temp_output = os.path.join(fileobj['dir'], 'output.mp4')

    cmd = f'"ffmpeg" -i "{temp_video}" -i "{temp_audio}" \
        -map 0:v -map 1:a -c copy -y "{temp_output}"'
    try:
        subprocess.call(cmd, shell=True)
        # 視訊檔重新命名
        os.rename(temp_output, os.path.join(fileobj['dir'], fileobj['name']))
        os.remove(temp_audio)
        os.remove(temp_video)
        print('視訊和聲音合併完成')
        # fileobj = {}
    except:
        print('視訊和聲音合併失敗')

def onProgress(stream, chunk, remains):
    total = stream.filesize
    percent = (total-remains) / total * 100
    print('下載中… {:05.2f}%'.format(percent), end='\r')

def download_sound():
    try:
        yt.streams.filter(type="audio").first().download()
    except:
        print('下載影片時發生錯誤，請確認網路連線和YouTube網址無誤。')
        return

# 檔案下載的回呼函式
def onComplete(stream, file_path):
    global download_count, fileobj
    fileobj['name'] = os.path.basename(file_path)
    fileobj['dir'] = os.path.dirname(file_path)
    print('\r')

    if download_count == 1:
        if check_media(file_path) == -1:
            print('此影片沒有聲音')
            download_count += 1
            try:
                # 視訊檔重新命名
                os.rename(file_path, os.path.join(
                    fileobj['dir'], 'temp_video.mp4'))
            except:
                print('視訊檔重新命名失敗')
                return

            print('準備下載聲音檔')
            download_sound()          # 下載聲音
        else:
            print('此影片有聲音，下載完畢！')
    else:
        try:
            # 聲音檔重新命名
            os.rename(file_path, os.path.join(
                fileobj['dir'], 'temp_audio.mp4'))
        except:
            print("聲音檔重新命名失敗")
        # 合併聲音檔
        merge_media()

def links_get(url):  # 取得播放清單所有影片網址的自訂函式
    urls = []   # 播放清單網址
    if '&list=' not in url :
        return urls    # 單一影片
    response = req.get(url)    # 發送 GET 請求
    if response.status_code != 200:
        print('請求失敗')
        return
    #請求成功, 解析網頁
    soup = BeautifulSoup(response.text, 'lxml')
    a_list = soup.find_all('a')
    base = 'https://www.youtube.com/'    # Youtube 網址
    for a in a_list:
        href = a.get('href')
        url = base + href  # 主網址結合 href 才是完整的影片網址
        if ('&index=' in url) and (url not in urls):
            urls.append(url)
    return urls

def video_download(url, listbox):
    # download_count = 1 #改回1
    print(url) #印出影片網址
    global yt
    yt = YouTube(url, on_progress_callback=onProgress,on_complete_callback=onComplete)
    name = yt.title
    no = listbox.size()     # 以目前列表框筆數為下載編號
    listbox.insert(tk.END, f'{no:02d}:{name}.....下載中')
    print('插入:', no, name)
    try:
        os.system('you-get ' +"\""+ url + "\"")
    except:
        try:
            print(yt.streams.filter(subtype='mp4',resolution="1080p")[0].download())
        except:
            print(yt.streams.filter(subtype='mp4',resolution="1080p")[1].download())
    print('更新:', no, name)
    listbox.delete(no)
    listbox.insert(no, f'{no:02d}:●{name}.....下載完成')
    # print(fileobj)
    return

#-------------------------------------------------------------------------
#------------主視窗------------#
win = tk.Tk()                          # 建立主視窗物件
win.geometry('640x480')                # 設定主視窗預設尺寸為640x480
win.resizable(False,False)             # 設定主視窗寬、高皆不可縮放
win.title('YouTube Video Downloader')  # 主視窗標題
win.iconbitmap('YouTube.ico')          # 主視窗icon
#------------ Label：顯示圖片 ------------#
img=Image.open("youtube.png")     
img=ImageTk.PhotoImage(img)
imLabel=tk.Label(win,image=img)
imLabel.pack()
#設定網址輸入區域
input_frm = tk.Frame(win, width=640, height=50)
input_frm.pack()
#設定提示文字
lb = tk.Label(input_frm, text='Type a link like a video or a playlist',
             fg='black')
lb.place(rely=0.2, relx=0.5, anchor='center')
#設定輸入框
input_url = tk.StringVar()     # 取得輸入的網址
input_et = tk.Entry(input_frm, textvariable=input_url, width=60)
input_et.place(rely=0.75, relx=0.5, anchor='center')
#設定按鈕
#-----------------------------------------------------------------

def btn_click():   # 按鈕的函式
    url = input_url.get()          # 取得文字輸入框的網址
    try:    #  測試 pytube 是否支援此網址或者網址是否正確
        YouTube(url)
    except:
        messagebox.showerror('錯誤','pytube 不支援此影片或者網址錯誤')
        return
    # pytube 支援此網址, 進行網路爬蟲
    urls = links_get(url)
    #輸入網址中有影片清單
    if urls and messagebox.askyesno('確認方塊',
            '是否下載清單內所有影片？(選擇 否(N) 會下載單一影片)') :
    #下載清單中所有影片
        print('開始下載清單')
        urls.sort(key = lambda s:int(re.search("index=\d+",s).group()[6:]))
        #對所有影片網址做排序

        for url in urls:     # 建立與啟動執行緒
            video_download(url, listbox)
    #下載單一影片
    else:
        yt = YouTube(url)
        if messagebox.askyesno('確認方塊',
                               f'是否下載{yt.title}影片？') :
            video_download(url, listbox)
        else:
            print('取消下載')

#-----------------------------------------------------------------
btn = tk.Button(input_frm, text='Download', command = btn_click,
                bg='orange', fg='Black')
btn.place(rely=0.75, relx=0.9, anchor='center')


#下載清單區域
dl_frm = tk.Frame(win, width=640, height=280)
dl_frm.pack()
#設定提示文字
lb = tk.Label(dl_frm, text='Download list',
              fg='black')
lb.place(rely=0.1, relx=0.5, anchor='center')
#設定顯示清單
listbox = tk.Listbox(dl_frm, width=65, height=15)
listbox.place(rely=0.6, relx=0.5, anchor='center')
#設定捲軸
sbar = tk.Scrollbar(dl_frm)
sbar.place(rely=0.6, relx=0.87, anchor='center', relheight=0.75)
#連結清單和捲軸
listbox.config(yscrollcommand = sbar.set)
sbar.config(command = listbox.yview)

#啟動主視窗
win.mainloop()
# Draw-and-Guess


## Introduction

Draw and Guess is a multiplayer game, developed using python `Kivy` library and socket programming. The rules are pretty much the same with Gartic.io, a more popular web-based draw and guess game, also the UI are almost the same.

## Preview

![](md_imgs/client%20screen1.png)

![](md_imgs/client%20waiting%20to%20start.png)

![](md_imgs/client%20guessing.png)

![](md_imgs/client%20show%20answer.png)

![](md_imgs/client%20selection.png)

## How to play

### Client app

Download the client files, and there's an executable file. Run that then you can play.

There are some chinese input error that I can't fix due to the sdl2 under setting stuffs.

### Server setup

Since there's no central server, you have to set up your own server in order to play with friends, just like how you play Minecraft multiplayer mode.

Download the server package, you will see 
1. `questions.txt`: The file you can modify all questions. 

2. `server_settings.json`: In which there are some basic server and game settings you can modify. The default port is set to `1234`
   
3. Some python files: The `server.py` is where you activate the server, and make sure you already installed python3 and configure the environmental variable.

> Network setting

Just like the way you setup Minecraft server. 

If you never setup a Minecraft server, there are 2 common approachs to connect with your friend. 

The first one is to use some virtual LAN services like `Hamachi`. The second one is to configure your router NAT, which can forword packets to the specific address and port in your LAN.

> Start the server

Open you cmd and cd to the server folder. By running this command `python server.py`, you should see `Server is running...`. Share your ip and port with your friend, and there you go! have fun with your friends!
#Simple chat using websockets and asyncio

import asyncio
import websockets
import time
import shlex


class Client:

    def __init__(self, server, websocket, path):

        '''Initialize a client'''

        self.client = websocket
        self.server = server
        self.name = None


    async def send(self, msg):

        '''Send message to client via websocket'''

        await self.client.send(msg)


    async def receive(self):

        '''Receive data from websocket'''

        msg = await self.client.recv()
        return msg


    async def handler(self):

        ''' Receive inputs from client and process it'''

        try:
            await self.send("Identify yourself with /name YourName")
            await self.send("/commands to show all comands")
            while True:
                msg = await self.receive()
                if msg:
                    print(f"{self.name} < {msg}")
                    await self.process_command(msg)
                else:
                    break
        except Exception:
            print("Error")
            raise
        finally: 
            self.server.disconnect(self)
    

    async def process_command(self, msg):

        '''Process inputs starting with a "/" (command), if its not 
        the case (its a message) just sends it to client via websocket.
        Also checks if the sending client have a name, if so send
        the message to all clients. If not, raise a warning.'''

        if msg.strip().startswith("/"):
            commands = shlex.split(msg.strip()[1:])
            if len(commands)==0:
                await self.send("Invalid command")
                return
            print(commands)
            command = commands[0].lower()            
            if command == "time":
                await self.send("Current time: " + time.strftime("%H:%M:%S"))
            elif command == "name":
                await self.change_nickname(commands)
            elif command == "private":
                await self.private_to(commands)
            elif command == "commands":
                await self.send("/name YourName to change your name")
                await self.send("/time to show current time")
                await self.send("/private Destination Message to send a private message")
            else:
                await self.send("Unknown command")
        else:
            if self.name:
                await self.server.send_all(self, msg)
            else:
                await self.send("Identify yourself before sending a message. Use /name YourName")


    async def change_nickname(self, commands):

        '''Verify if client didnt inputed a empty string and if the
        nickname is already in use. After the verification the
        client name is changed.'''

        if len(commands)>1 and self.server.verify_nickname(commands[1]):
            self.name = commands[1]
            await self.send(f"Successfully changed nickname to {self.name}")
            await self.server.send_all(self,f"{self.name} just joined this chat.")
        else:
            await self.send("Username in use. Please try again.")


    async def private_to(self, command):

        '''Verify if the command was correctly used. Separete command 
        argument into variables and sends to destination'''

        if len(command)<3:
            await self.send("Invalid command. Use /private nickname message")
            return
        destination = command[1]
        msg = " ".join(command[2:])
        sent = await self.server.send_to_destination(self, msg, destination)
        if not sent:
            await self.send(f"Destination {destination} not found. Message not sent")


    @property
    def connected(self):
        return self.client.open

class Server:
    def __init__(self):
       
        '''Initialize the class and a empty list for active connections'''
        
        self.connections = []
    

    def verify_nickname(self, name):

        ''' Verifies if inputed name is in active connections'''

        for client in self.connections:
            if client.name and client.name == name:
                return False
        return True


    async def connect(self, websocket, path):
        '''Accept connection from a websocket and add it to the
        list of active connections '''
       
        client = Client(self, websocket, path)
        if client not in self.connections:
            self.connections.append(client)
            print(f"New client connected. Total: {self.nconnections}")
        await client.handler()
    

    async def disconnect(self, client):

        ''' Remove selected client from the list of active connections'''
        
        if client in self.connections:
            self.connections.remove(client)
        print(f"Client {client.name} disconnected. Remaining {self.nconnections} active.")


    async def send_all(self, origin, msg):
        
        ''' Checks if the current client is the author of the
        message and if all others still connected, then sends msg'''

        print("Sending all")
        for client in self.connections:
            if origin != client and client.connected:
                print(f"[Sending] {origin.name} >> {client.name}: {msg}")
                await client.send(f"[ALL] {origin.name} >> {msg}")
                


    async def send_to_destination(self, origin, msg, destination):
        
        ''' Checks if the current client is the destination, still
        connected and isnt the origin of the message'''

        for client in self.connections:
            if origin != client and client.connected and client.name == destination:
                print(f"[Sending] {origin.name} >> {client.name}: {msg}")
                await client.send(f"[PRIVATE] {origin.name} >> {msg}")
                return True
        return False

        
    @property
    def nconnections(self):
        
        '''Return the number of active connections'''
       
        return(len(self.connections))
    
    
    
#Starting server

server = Server() 
loop = asyncio.get_event_loop()
start_server = websockets.serve(server.connect, 'localhost', 8888) 

loop.run_until_complete(start_server)
loop.run_forever()


import discord
from discord.ext import commands
import os, requests, json, random, asyncio, aiohttp
from replit import db
import music
from requests import Session
from random import randint
from stayAlive import keep_alive
import http.client, urllib.parse

cogs = [music]

client = commands.Bot(command_prefix=',', intents=discord.Intents.all())

for i in range(len(cogs)):
  asyncio.run(cogs[i].setup(client))

feelings = ['sad', 'bad', 'dejected', 'depressed', 'horrible', 'upset']

@client.command(name='test', aliases=['tes'])
async def test(ctx, arg):
  await ctx.send(arg)

encouragements = [
  'You will be just fine!',
  'Grow the fuck up',
  'Cheer up!',
  'Do not commit suicide please'
]

if 'responding' not in db.keys():
  db['responding'] = True


def updateEncouragements(newQuote):
  if 'encouragements' in db.keys():
    encouragement = db['encouragements']
    encouragement.append(newQuote)
    db['encouragements'] = encouragement
  else:
    db['encouragements'] = [newQuote]

def deleteEncouragement(index):
  encouragement = db['encouragements']
  if len(encouragement) > index and index > 0:
    encouragement.pop(index)
    db['encouragements'] = encouragement


@client.event
async def on_ready():
  print(f'Logged in as {client.user}')
  channel = client.get_channel(1010563742444028016)
  await channel.send('I am alive')

@client.event
async def on_message(message):
  if message.author == client.user:
    return

  if db['responding']:
    quotes = encouragements
    if 'encouragements' in db.keys():
      quotes += db['encouragements']
    
    if any(word in message.content for word in feelings):
      await message.channel.send(random.choice(quotes))

  if message.content.startswith('qshow'):
    quoteList = []
    if 'encouragements' in db.keys():
      quoteList = db['encouragements'].value
      await message.channel.send(quoteList)
  
  if message.content.startswith('qnew'):
    newQuote = message.content.split('qnew', 1)[1]
    updateEncouragements(newQuote)
    await message.channel.send("New encouragement added!")

  if message.content.startswith('qdelete'):
    encourageList = []
    if 'encouragements' in db.keys():
      index = int(message.content.split('qdelete', 1)[1])
      deleteEncouragement(index)
      encourageList = db['encouragements'].value
    await message.channel.send(encourageList)

  if message.content.startswith('hresponding'):
    value = message.content.split('hresponding ', 1)[1]

    if value.lower() == "true":
      db["responding"] = True
      await message.channel.send("Encouraging responses are now on.")
    else:
      db['responding'] = False
      await message.channel.send('Encouraging responses are now off.')
      
  # will not let any command process otherwise(so i am overriding the default on_message)
  await client.process_commands(message)

@client.command()
async def ping(self, ctx):
  await ctx.send(f"Pong!, {round(client.latency * 1000)} ms")
      
@client.command(name="cointoss", help="Tosses coins for you. Optional: Add number of cointosses you need")
async def cointoss(ctx, times = 0):
    if times == 0 or times == 1:
        result = randint(0, 1)
        if result == 0:
          await ctx.send(":wind_blowing_face: Heads")
        else:
          await ctx.send(":wind_blowing_face: Tails")
    
    elif times > 10000 or times < 0 or type(times) != int:
        await ctx.send("Please enter a valid number")

    else:
        n, heads, tails = 0, 0, 0
        while(n < times):
            result = randint(0, 1)
            if result == 0:
                heads += 1
            else:
                tails += 1
            n += 1

        await ctx.send("Your " + str(times) + " :coin: tosses got you " + str(heads) + " heads and " + str(tails) + " tails.")

@client.command(name = "crypto", help="Gets the latest price of any cryptocurrency", aliases=['cprice', 'cp'])
async def cryptoPrice(ctx, *, currency):
    currency = currency.replace(' ', '-')
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest' # Coinmarketcap API url
    parameters = { 'slug': currency, 'convert': 'USD' } # API parameters to pass in for retrieving specific cryptocurrency data; slug is the informal currency name while 'convert' is the currency I am gonna use

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': '%s'%os.getenv('CMC')
    } # my api key 

    session = Session()
    session.headers.update(headers)

    response = session.get(url, params=parameters)

    info = json.loads(response.text)
    id = list(json.loads(response.text)['data'].keys())[0]
    name = info['data'][id]['name'] 
    price = info['data'][id]['quote']['USD']['price']
    await ctx.send('The price of **' + name + '** today is **' + str(round(price, 4)) + ' United States Dollar**')

@client.command(name='quote', help='Draws quotes from zenquotes')
async def quote(ctx):
    try:
      response = requests.get('https://zenquotes.io/api/random')
      json_data = json.loads(response.text)
      quote = '"' + json_data[0]['q'] + '"'
      author = "- " + json_data[0]['a']
      quoteEmbed = discord.Embed(title=quote, description='**' + author + '**', color=discord.Colour.random())
      quoteEmbed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
      await ctx.send(embed=quoteEmbed)
    except:  
      print("Error!")

@client.command(name='8ball', help="Ask 8ball about all your life related queries ")
async def __8ball(ctx, *, doubt):
    conn = http.client.HTTPSConnection("8ball.delegator.com")
    question = urllib.parse.quote(doubt)
    conn.request('GET', '/magic/JSON/' + question)
    response = conn.getresponse()
    await ctx.send("**8ball:** " + json.loads(response.read())['magic']['answer'])

# XKCD functionality

async def fetch(session, url):
    response = await session.get(url)
    await session.close()
    try:
        return await response.json()
    except aiohttp.ContentTypeError:
        return None

async def get_xkcd(_id: int):
    return await fetch(aiohttp.ClientSession(), f"http://xkcd.com/{_id}/info.0.json")

async def get_latest():
    return await fetch(aiohttp.ClientSession(), f"http://xkcd.com/info.0.json")

def generate_embed(data):
    title = f'xkcd #{data.get("num")} - {data.get("title")}'
    embed = discord.Embed(title=title, url=f'https://xkcd.com/{data.get("num")}', description="%s"%data.get('alt'))
    embed.set_image(url=data.get("img"))
    return embed

async def get_max_xkcd():
    data = await get_latest()
    return data.get("num")

@client.command(name='xkcd', help='Fetches random comics from www.xkcd.com')
async def __randomXKCD(ctx):
    max_xkcd = await get_max_xkcd()
    _id = random.randint(1, max_xkcd)
    data = await get_xkcd(_id)
    embed = generate_embed(data)
    await ctx.send(embed=embed)

# shows kat
@client.command(name="cat", help="Get yourself some cats")
async def cat(ctx):
    data = requests.get("https://api.thecatapi.com/v1/images/search")
    data = data.json()
    get = data[0]
    result = get["url"]
    embed = discord.Embed(
        title="Here is a cat",
        color=discord.Color.random()
    )
    embed.set_image(url=result)
    await ctx.send(embed=embed)

@client.command(name='weather', help="Shows the current weather of a city")
async def getWeather(ctx, *, city):
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather?"
    City = str(city)
    URL = BASE_URL + "q={}".format(City) + "&appid=" + os.getenv('weather') + '&units=metric'
    # HTTP request
    response = requests.get(URL)
    if response.status_code == 200:
      print("Collecting json")
      data = response.json()
      
      main = data['main']
      temperature = main['temp']
      humidity = main['humidity']
      pressure = main['pressure']
      report = data['weather']
      print("Collected data")
      embed = discord.Embed(
        title="Current weather :cloud_tornado: in " + city + " is:", description=report[0]['main'] + " (" + report[0]['description'] + ")",
        color=discord.Color.random()
      )
      embed.set_thumbnail(url="http://openweathermap.org/img/w/{}.png".format(str(report[0]['icon'])))
      embed.add_field(name='Temperature(°C):', value=temperature, inline=False)
      embed.add_field(name='Humidity:', value=str(humidity) + '%', inline=False)
      embed.add_field(name='Wind Speed', value=str(data['wind']['speed']) + " meters/ second", inline=False)
      embed.add_field(name='Pressure:', value=str(pressure) + ' millibars', inline=False)
      embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)

      await ctx.send(embed=embed)
    else:
      # showing the error message
      embed = discord.Embed(
        title="No such city was found!",
        color=discord.Color.random()
      )
      await ctx.send(embed=embed)



class MyHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        e = discord.Embed(color=discord.Color.blurple(), description='')
        for page in self.paginator.pages:
            e.description += page
        await destination.send(embed=e)
    help_command = commands.DefaultHelpCommand(
    no_category = 'Commands'
)

client.help_command = MyHelpCommand()

keep_alive()
try:
  client.run(os.getenv('TOKEN'))
except:
  os.system('kill 1')
# using uptimerobot.com to ping our flask webserver once every five minutes

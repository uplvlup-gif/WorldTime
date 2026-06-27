import discord
from discord.ext import tasks
import datetime
import pytz
import asyncio

# ==================== CONFIGURATION ====================
TOKEN = "MTUyMDM3ODkyNDIzOTE1OTQ3OA.G5CwEL.68nrTwCe1pKx4fHmNSfTGQ10XLU6XNnv33_WO4"          # Paste your Developer Portal bot token here
CHANNEL_ID = 123456789012345678          # Paste your #world-chart channel ID here
# =======================================================

# Complete mapping of your 38 unique Discord roles to global time databases
TIMEZONE_MAP = {
    # --- Western Hemisphere ---
    "GMT -12 / Baker Island (AoE)": "Etc/GMT+12",
    "GMT -11 / Samoa (SST)": "Pacific/Pago_Pago",
    "GMT -10 / Hawaii (HST)": "Pacific/Honolulu",
    "GMT -9:30 / Marquesas Islands (MART)": "Pacific/Marquesas",
    "GMT -9 / Alaska (AKST)": "America/Anchorage",
    "GMT -8 / Pacific (PST)": "America/Los_Angeles",
    "GMT -7 / Mountain (MST)": "America/Denver",
    "GMT -6 / Central (CST)": "America/Chicago",
    "GMT -5 / Eastern (EST)": "America/New_York",
    "GMT -4 / Atlantic (AST)": "America/Halifax",
    "GMT -3:30 / Newfoundland (NST)": "America/St_Johns",
    "GMT -3 / Brazil (BRT)": "America/Sao_Paulo",
    "GMT -2 / South Georgia (GST)": "Atlantic/South_Georgia",
    "GMT -1 / Azores (AZOT)": "Atlantic/Azores",
    "GMT / UTC +0 (WET / GMT)": "Europe/London",
    "GMT +1 / Central Europe (CET)": "Europe/Warsaw",
    "GMT +2 / Eastern Europe (EET)": "Europe/Kyiv",
    "GMT +3 / East Africa (EAT)": "Europe/Istanbul",
    
    # --- Eastern Hemisphere ---
    "GMT +3:30 / Iran (IRST)": "Asia/Tehran",
    "GMT +4 / Gulf (GST)": "Asia/Dubai",
    "GMT +4:30 / Afghanistan (AFT)": "Asia/Kabul",
    "GMT +5 / Pakistan (PKT)": "Asia/Karachi",
    "GMT +5:30 / India (IST)": "Asia/Kolkata",
    "GMT +5:45 / Nepal (NPT)": "Asia/Kathmandu",
    "GMT +6 / Bangladesh (BST)": "Asia/Dhaka",
    "GMT +6:30 / Myanmar (MMT)": "Asia/Yangon",
    "GMT +7 / Indochina (ICT)": "Asia/Bangkok",
    "GMT +8 / China / West Australia (CST / AWST)": "Asia/Shanghai",
    "GMT +8:45 / Eucla (ACWST)": "Australia/Eucla",
    "GMT +9 / Japan / Korea (JST / KST)": "Asia/Tokyo",
    "GMT +9:30 / Central Australia (ACST)": "Australia/Darwin",
    "GMT +10 / East Australia (AEST)": "Australia/Sydney",
    "GMT +10:30 / Lord Howe Island (LHST)": "Australia/Lord_Howe",
    "GMT +11 / Solomon Islands (SBT)": "Asia/Guadalcanal",
    "GMT +12 / New Zealand (NZST)": "Pacific/Auckland",
    "GMT +12:45 / Chatham Islands (CHAST)": "Pacific/Chatham",
    "GMT +13 / Tonga (TOT)": "Pacific/Tongatapu",
    "GMT +14 / Line Islands (LINT)": "Pacific/Kiritimati"
}

intents = discord.Intents.default()
intents.members = True          # Allows reading member list data
intents.message_content = True  # Allows managing content layouts
client = discord.Client(intents=intents)
chart_message = None

@client.event
async def on_ready():
    print(f"✅ Logged in successfully as {client.user.name}")
    print("🌍 Initializing global timezone sync loop...")
    update_chart.start()

@tasks.loop(minutes=5)
async def update_chart():
    global chart_message
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print(f"❌ Error: Channel ID {CHANNEL_ID} not found. Verify bot channel access.")
        return

    guild = channel.guild
    
    # We use two separate embedded messages because Discord has a 6000 character limit per embed
    embed_west = discord.Embed(
        title="📊 GLOBAL SERVER DIRECTORY (WEST)", 
        color=0x3498db,
        description="Live directory tracking our Western Hemisphere community distribution and active hours.\n\u200b"
    )
    embed_east = discord.Embed(
        title="📊 GLOBAL SERVER DIRECTORY (EAST)", 
        color=0xe67e22,
        description="Live directory tracking our Eastern Hemisphere community distribution and active hours.\n\u200b"
    )

    is_eastern = False

    for role_name, tz_string in TIMEZONE_MAP.items():
        # Switch target container when reaching the eastern list division marker
        if role_name == "GMT +3:30 / Iran (IRST)":
            is_eastern = True

        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            try:
                # Calculate active time metrics per region string
                tz = pytz.timezone(tz_string)
                local_time = datetime.datetime.now(tz).strftime("%I:%M %p")
                
                # Fetch human users assigned to role strings (ignores integrated applications/bots)
                members = [member.mention for member in role.members if not member.bot]
                
                # Format directory data fields strings
                if members:
                    member_list = ", ".join(members)
                    count_suffix = f"({len(members)} active)"
                else:
                    member_list = "*No active members*"
                    count_suffix = ""

                target_embed = embed_east if is_eastern else embed_west
                target_embed.add_field(
                    name=f"{role_name} — 🕒 {local_time} {count_suffix}",
                    value=f"{member_list}\n\u200b",
                    inline=False
                )
            except Exception as e:
                print(f"⚠️ Error parsing timezone {tz_string}: {e}")

    # Track message objects to perform background text modifications instead of duplicate posting
    try:
        messages_to_send = [embed_west, embed_east]
        
        # Look for existing messages posted by this bot token to update cleanly
        bot_messages = []
        async for msg in channel.history(limit=20):
            if msg.author == client.user:
                bot_messages.append(msg)
        
        # Reverse list to keep the chronological ordering correct
        bot_messages.reverse()

        if len(bot_messages) >= 2:
            await bot_messages[0].edit(embed=embed_west)
            await bot_messages[1].edit(embed=embed_east)
            print("🔄 Timezone chart successfully updated and synced.")
        else:
            # Purge channel debris and establish fresh structural anchors if missing
            await channel.purge(limit=10, check=lambda m: m.author == client.user)
            await channel.send(embed=embed_west)
            await channel.send(embed=embed_east)
            print("✨ Fresh database charts deployed to tracking channel.")
            
    except discord.errors.HTTPException as http_err:
        print(f"❌ Discord API limit threshold reached: {http_err}")

# Execute main wrapper runtime instance
if __name__ == "__main__":
    client.run(TOKEN)

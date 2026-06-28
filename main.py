import os
import discord
from discord.ext import tasks
import datetime
import pytz
import asyncio

# ==================== CONFIGURATION ====================
TOKEN = os.environ.get("DISCORD_TOKEN")   # Kept secure for Railway environment injection
CHANNEL_ID = 1511642944891916378           # Replace with your actual #world-chart channel ID
# =======================================================


# Mapping your unique Discord roles to global time zones
TIMEZONE_MAP = {
    # --- Western Hemisphere ---
    "GMT -12 / Baker Island (AoE)": "Etc/GMT+12",
    "GMT -11 / Samoa (SST)": "Pacific/Pago_Pago",
    "GMT -10 / Hawaii (HST)": "Pacific/Honolulu",
    "GMT -9:30 / Marquesas Islands (MART)": "Pacific/Marquesas",
    "GMT -9 / Alaska (AKST)": "America/Anchorage",
    "GMT -8 / Pacific (PST)": "America/Los_Angeles",
    "GMT -7 / Mountain (MST)": "America/Denver",
    "GMT -7 / Arizona (MST)": "America/Phoenix",
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
    "GMT +11 / Solomon Islands (SBT)": "Pacific/Guadalcanal",
    "GMT +12 / New Zealand (NZST)": "Pacific/Auckland",
    "GMT +12:45 / Chatham Islands (CHAST)": "Pacific/Chatham",
    "GMT +13 / Tonga (TOT)": "Pacific/Tongatapu",
    "GMT +14 / Line Islands (LINT)": "Pacific/Kiritimati"
}

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
client = discord.Client(intents=intents)
chart_message = None

@client.event
async def on_ready():
    print(f"✅ Logged in successfully as {client.user.name}")
    print("🌍 Initializing live DST-aware tracking string loops...")
    update_chart.start()

# ==================== NEW AUTOMATIC ROLE SWAPPER ====================
@client.event
async def on_raw_reaction_add(payload):
    # Ignore reactions made by the bot itself to prevent infinite processing loops
    if payload.user_id == client.user.id:
        return

    guild = client.get_guild(payload.guild_id)
    if not guild:
        return

    member = guild.get_member(payload.user_id)
    if not member:
        return

    # Check if the user holds the target missing timezone tag
    missing_role = discord.utils.get(guild.roles, name="MissingTimezone")
    if not missing_role or missing_role not in member.roles:
        return

    # Scan through your 38 roles to see if the emoji clicked matches a timezone role
    for role_name in TIMEZONE_MAP.keys():
        target_role = discord.utils.get(guild.roles, name=role_name)
        if target_role:
            # If the user just gained a valid timezone, immediately strip the tracking tag
            if target_role in member.roles:
                try:
                    await member.remove_roles(missing_role)
                    print(f"⚡ Python auto-stripped 'Missing Timezone' role from {member.name}!")
                    break
                except discord.errors.Forbidden:
                    print("❌ Permission Error: Move the bot's role HIGHER up in Server Settings > Roles!")
# ====================================================================

@tasks.loop(minutes=5)
async def update_chart():
    global chart_message
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        return

    guild = channel.guild
    
    embed_west = discord.Embed(
        title="📊 GLOBAL SERVER DIRECTORY (WEST)", 
        color=0x3498db,
        description="Live tracking dashboard showing our Western Hemisphere community distribution and dynamic active hours.\n\u200b"
    )
    embed_east = discord.Embed(
        title="📊 GLOBAL SERVER DIRECTORY (EAST)", 
        color=0xe67e22,
        description="Live tracking dashboard showing our Eastern Hemisphere community distribution and dynamic active hours.\n\u200b"
    )

    is_eastern = False

    for role_name, tz_string in TIMEZONE_MAP.items():
        if role_name == "GMT +3:30 / Iran (IRST)":
            is_eastern = True

        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            try:
                # 🔄 FORCE CACHE RELOAD: Downloads all member details to prevent raw number bugs
                await guild.chunk() 

                tz = pytz.timezone(tz_string)
                now_localized = datetime.datetime.now(tz)
                local_time = now_localized.strftime("%I:%M %p")
                active_abbreviation = now_localized.strftime("%Z")
                
                display_title = role_name
                replacements = {
                    "(PST)": f"({active_abbreviation})", "(MST)": f"({active_abbreviation})",
                    "(CST)": f"({active_abbreviation})", "(EST)": f"({active_abbreviation})",
                    "(AST)": f"({active_abbreviation})", "(WET / GMT)": f"({active_abbreviation})",
                    "(CET)": f"({active_abbreviation})", "(EET)": f"({active_abbreviation})",
                    "(AEST)": f"({active_abbreviation})", "(NZST)": f"({active_abbreviation})"
                }
                
                for static_tag, dynamic_tag in replacements.items():
                    if static_tag in display_title:
                        display_title = display_title.replace(static_tag, dynamic_tag)
                
                # FIXED: Changed back to member.mention for fully clickable tags!
                members = [member.mention for member in role.members if not member.bot]
                
                if members:
                    member_list = ", ".join(members)
                    count_suffix = f"({len(members)} active)"
                else:
                    member_list = "*No active members*"
                    count_suffix = ""

                target_embed = embed_east if is_eastern else embed_west
                target_embed.add_field(
                    name=f"{display_title} — 🕒 {local_time} {count_suffix}",
                    value=f"{member_list}\n\u200b",
                    inline=False
                )

            except Exception as e:
                print(f"⚠️ Error parsing timezone {tz_string}: {e}")

        # Track message objects to perform background text modifications instead of duplicate posting
    try:
        # Scan channel log strings to fetch the target containers
        bot_messages = []
        async for msg in channel.history(limit=20):
            if msg.author == client.user:
                bot_messages.append(msg)
        
        # Sort chronologically so West sits cleanly on top of East
        bot_messages.reverse()

        # If both placeholder targets are present, edit them seamlessly
        if len(bot_messages) >= 2:
            await bot_messages[0].edit(embed=embed_west)
            await bot_messages[1].edit(embed=embed_east)
            print("🔄 Timezone chart updated as a single seamless directory split.")
        else:
            # If a structural target message was deleted, purge layout fragments and re-anchor
            await channel.purge(limit=10, check=lambda m: m.author == client.user)
            await channel.send(embed=embed_west)
            await channel.send(embed=embed_east)
            print("✨ Fresh data layouts deployed to tracking window.")
            
    except discord.errors.HTTPException as http_err:
        print(f"❌ Discord API limit threshold reached: {http_err}")


if __name__ == "__main__":
    client.run(TOKEN)

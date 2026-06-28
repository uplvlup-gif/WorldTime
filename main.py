import os
import discord
from discord.ext import tasks
import datetime
import pytz
import asyncio
import folium
import requests
import base64

# ==================== CONFIGURATION ====================
TOKEN = os.environ.get("DISCORD_TOKEN")   
CHANNEL_ID = 1511642944891916378           
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
# =======================================================

TIMEZONE_MAP = {
    # --- Western Hemisphere ---
    "GMT -12 / Baker Island (AoE)": {"tz": "Etc/GMT+12", "lat": -0.19, "lon": -176.47, "label": "Baker Island"},
    "GMT -11 / Samoa (SST)": {"tz": "Pacific/Pago_Pago", "lat": -14.27, "lon": -170.70, "label": "Samoa"},
    "GMT -10 / Hawaii (HST)": {"tz": "Pacific/Honolulu", "lat": 21.30, "lon": -157.85, "label": "Hawaii"},
    "GMT -9:30 / Marquesas Islands (MART)": {"tz": "Pacific/Marquesas", "lat": -9.00, "lon": -139.50, "label": "Marquesas"},
    "GMT -9 / Alaska (AKST)": {"tz": "America/Anchorage", "lat": 61.21, "lon": -149.90, "label": "Alaska"},
    "GMT -8 / Pacific (PST)": {"tz": "America/Los_Angeles", "lat": 34.05, "lon": -118.24, "label": "US Pacific"},
    "GMT -7 / Mountain (MST)": {"tz": "America/Denver", "lat": 39.73, "lon": -104.99, "label": "US Mountain"},
    "GMT -7 / Arizona (MST)": {"tz": "America/Phoenix", "lat": 33.44, "lon": -112.07, "label": "Arizona"},
    "GMT -6 / Central (CST)": {"tz": "America/Chicago", "lat": 41.87, "lon": -87.62, "label": "US Central"},
    "GMT -5 / Eastern (EST)": {"tz": "America/New_York", "lat": 40.71, "lon": -74.00, "label": "US Eastern"},
    "GMT -4 / Atlantic (AST)": {"tz": "America/Halifax", "lat": 44.65, "lon": -63.57, "label": "Atlantic Canada"},
    "GMT -3:30 / Newfoundland (NST)": {"tz": "America/St_Johns", "lat": 47.56, "lon": -52.71, "label": "Newfoundland"},
    "GMT -3 / Brazil (BRT)": {"tz": "America/Sao_Paulo", "lat": -23.55, "lon": -46.63, "label": "Brazil"},
    "GMT -2 / South Georgia (GST)": {"tz": "Atlantic/South_Georgia", "lat": -54.28, "lon": -36.50, "label": "South Georgia"},
    "GMT -1 / Azores (AZOT)": {"tz": "Atlantic/Azores", "lat": 37.74, "lon": -25.66, "label": "Azores"},
    "GMT / UTC +0 (WET / GMT)": {"tz": "Europe/London", "lat": 51.50, "lon": -0.12, "label": "UK / GMT"},
    "GMT +1 / Central Europe (CET)": {"tz": "Europe/Warsaw", "lat": 52.23, "lon": 21.01, "label": "Central Europe"},
    "GMT +2 / Eastern Europe (EET)": {"tz": "Europe/Kyiv", "lat": 50.45, "lon": 30.52, "label": "Eastern Europe"},
    "GMT +3 / East Africa (EAT)": {"tz": "Europe/Istanbul", "lat": 41.00, "lon": 28.97, "label": "Turkey / East Africa"},
    
    # --- Eastern Hemisphere ---
    "GMT +3:30 / Iran (IRST)": {"tz": "Asia/Tehran", "lat": 35.68, "lon": 51.38, "label": "Iran"},
    "GMT +4 / Gulf (GST)": {"tz": "Asia/Dubai", "lat": 25.20, "lon": 55.27, "label": "Gulf States"},
    "GMT +4:30 / Afghanistan (AFT)": {"tz": "Asia/Kabul", "lat": 34.53, "lon": 69.16, "label": "Afghanistan"},
    "GMT +5 / Pakistan (PKT)": {"tz": "Asia/Karachi", "lat": 24.86, "lon": 67.00, "label": "Pakistan"},
    "GMT +5:30 / India (IST)": {"tz": "Asia/Kolkata", "lat": 22.57, "lon": 88.36, "label": "India"},
    "GMT +5:45 / Nepal (NPT)": {"tz": "Asia/Kathmandu", "lat": 27.71, "lon": 85.32, "label": "Nepal"},
    "GMT +6 / Bangladesh (BST)": {"tz": "Asia/Dhaka", "lat": 23.81, "lon": 90.41, "label": "Bangladesh"},
    "GMT +6:30 / Myanmar (MMT)": {"tz": "Asia/Yangon", "lat": 16.86, "lon": 96.19, "label": "Myanmar"},
    "GMT +7 / Indochina (ICT)": {"tz": "Asia/Bangkok", "lat": 13.75, "lon": 100.50, "label": "Indochina"},
    "GMT +8 / China / West Australia (CST / AWST)": {"tz": "Asia/Shanghai", "lat": 31.23, "lon": 121.47, "label": "China / WA"},
    "GMT +8:45 / Eucla (ACWST)": {"tz": "Australia/Eucla", "lat": -31.67, "lon": 128.88, "label": "Eucla"},
    "GMT +9 / Japan / Korea (JST / KST)": {"tz": "Asia/Tokyo", "lat": 35.67, "lon": 139.65, "label": "Japan / Korea"},
    "GMT +9:30 / Central Australia (ACST)": {"tz": "Australia/Darwin", "lat": -12.46, "lon": 130.84, "label": "Central Australia"},
    "GMT +10 / East Australia (AEST)": {"tz": "Australia/Sydney", "lat": -33.86, "lon": 151.20, "label": "East Australia"},
    "GMT +10:30 / Lord Howe Island (LHST)": {"tz": "Australia/Lord_Howe", "lat": -31.55, "lon": 159.08, "label": "Lord Howe Island"},
    "GMT +11 / Solomon Islands (SBT)": {"tz": "Pacific/Guadalcanal", "lat": -9.57, "lon": 160.14, "label": "Solomon Islands"},
    "GMT +12 / New Zealand (NZST)": {"tz": "Pacific/Auckland", "lat": -36.84, "lon": 174.76, "label": "New Zealand"},
    "GMT +12:45 / Chatham Islands (CHAST)": {"tz": "Pacific/Chatham", "lat": -43.95, "lon": -176.56, "label": "Chatham Islands"},
    "GMT +13 / Tonga (TOT)": {"tz": "Pacific/Tongatapu", "lat": -21.17, "lon": -175.20, "label": "Tonga"},
    "GMT +14 / Line Islands (LINT)": {"tz": "Pacific/Kiritimati", "lat": 1.87, "lon": -157.36, "label": "Line Islands"}
}

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
client = discord.Client(intents=intents, chunk_guilds_at_startup=True)

@client.event
async def on_ready():
    print(f"✅ Logged in successfully as {client.user.name}")
    print("🌍 Starting combined Discord Embed & GitHub Map loops...")
    if not update_chart.is_running():
        update_chart.start()

def push_map_to_github(html_content):
    """Encodes and forces a push of our interactive map layout directly into the repository."""
    if not GITHUB_TOKEN:
        print("⚠️ GitHub generation skipped: Missing GITHUB_TOKEN environment setup.")
        return

    # 🛠️ HARDCODED SECURE GITHUB Rest API PATHWAYS (Bypasses variable composition bugs)
    url_get = "https://github.com"
    url_put = "https://github.com"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        # Appends a unique cache-buster parameter to guarantee live server delivery
        cache_bust_url = f"{url_get}?t={int(datetime.datetime.now(datetime.UTC).timestamp())}"
        response = requests.get(cache_bust_url, headers=headers)
        
        sha = None
        if response.status_code == 200:
            sha = response.json().get("sha")

        encoded_content = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": f"🤖 Dynamic World Map Sync: {datetime.datetime.now(datetime.UTC)} UTC",
            "content": encoded_content
        }
        if sha:
            payload["sha"] = sha

        put_response = requests.put(url_put, headers=headers, json=payload)
        
        if put_response.status_code == 200 or put_response.status_code == 201:
            print("🌐 SUCCESS: Interactive web map has been successfully updated on your GitHub branch!")
        else:
            print(f"❌ GitHub Deployment Failure: {put_response.status_code} - {put_response.text}")
            
    except Exception as e:
        print(f"❌ Critical error executing GitHub API sync pipeline: {e}")


@tasks.loop(minutes=5)
async def update_chart():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        return

    guild = channel.guild
    roles_by_name = {role.name: role for role in guild.roles}
    
    world_map = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

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
    replacements = ["(PST)", "(MST)", "(CST)", "(EST)", "(AST)", "(WET / GMT)", "(CET)", "(EET)", "(AEST)", "(NZST)"]

    for role_name, info in TIMEZONE_MAP.items():
        if role_name == "GMT +3:30 / Iran (IRST)":
            is_eastern = True

        role = roles_by_name.get(role_name)
        if role:
            try:
                tz = pytz.timezone(info["tz"])
                now_localized = datetime.datetime.now(tz)
                local_time = now_localized.strftime("%I:%M %p")
                active_abbreviation = now_localized.strftime("%Z")
                
                display_title = role_name
                for static_tag in replacements:
                    if static_tag in display_title:
                        display_title = display_title.replace(static_tag, f"({active_abbreviation})")
                        break
                
                members = [member.mention for member in role.members if not member.bot]
                member_count = len(members)

                if member_count > 0:
                    clean_display_names = [member.display_name for member in role.members if not member.bot]
                    popup_markup = f"""<b>📍 {info['label']}</b><br>
🕒 Time: {local_time}<br>
👥 Count: {member_count}<br><br>
""" + ", ".join(clean_display_names)
                    
                    folium.CircleMarker(
                        location=[info["lat"], info["lon"]],
                        radius=8 + (member_count * 1.5),
                        popup=folium.Popup(popup_markup, max_width=280),
                        color="#3498db" if not is_eastern else "#e67e22",
                        fill=True,
                        fill_opacity=0.55
                    ).add_to(world_map)

                if members:
                    member_list = ", ".join(members)
                    count_suffix = f"({member_count} active)"
                else:
                    member_list = "*No active members*"
                    count_suffix = ""

                target_embed = embed_east if is_eastern else embed_west
                target_embed = embed_east if is_eastern else embed_west
                target_embed.add_field(
                    name=f"{display_title} — 🕒 {local_time} {count_suffix}",
                    value=f"{member_list}\n\u200b",
                    inline=False
                )
            except Exception as e:
                print(f"⚠️ Error parsing processing matrix for zone {info['tz']}: {e}")

    # Generate the map structure and export to GitHub API endpoints
    map_html = world_map._repr_html_()
    push_map_to_github(map_html)

    # In-place background Discord text modifications
    try:
        bot_messages = []
        async for msg in channel.history(limit=10):
            if msg.author == client.user:
                bot_messages.append(msg)
                if len(bot_messages) == 2:
                    break
        
        bot_messages.reverse()

        if len(bot_messages) >= 2:
            await bot_messages[0].edit(embed=embed_west)
            await bot_messages[1].edit(embed=embed_east)
            print("🔄 Timezone chart updated seamlessly across directory split.")
        else:
            # FIX: Safe message recreation without breaking tracking loop anchoring logic
            for old_msg in bot_messages:
                try:
                    await old_msg.delete()
                except discord.HTTPException:
                    pass
            await channel.send(embed=embed_west)
            await channel.send(embed=embed_east)
            print("✨ Fresh data layouts deployed to tracking window.")
            
    except discord.errors.HTTPException as http_err:
        print(f"❌ Discord API limit threshold reached: {http_err}")

if __name__ == "__main__":
    client.run(TOKEN)

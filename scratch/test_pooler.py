import asyncio
import asyncpg
import socket

async def main():
    # First, check DNS resolution for different hosts
    hosts_to_test = [
        ("Direct", "db.qagextokkrxrrmowyser.supabase.co"),
        ("Pooler", "aws-0-ap-south-1.pooler.supabase.com"),
    ]
    
    for label, host in hosts_to_test:
        try:
            # Try IPv4
            results = socket.getaddrinfo(host, 5432, socket.AF_INET)
            ip = results[0][4][0] if results else "No IPv4"
            print(f"{label} ({host}): IPv4 = {ip}")
        except:
            print(f"{label} ({host}): No IPv4 resolution")
        try:
            results = socket.getaddrinfo(host, 5432, socket.AF_INET6)
            ip = results[0][4][0] if results else "No IPv6"
            print(f"{label} ({host}): IPv6 = {ip}")
        except:
            print(f"{label} ({host}): No IPv6 resolution")
    
    print("\n--- Connection Tests ---\n")
    
    # Test 1: Direct connection with postgres user (will need password)
    # Test 2: Pooler with postgres user (port 6543, transaction mode)
    # Test 3: Pooler with postgres user (port 5432, session mode)
    
    tests = [
        ("Pooler-Transaction (port 6543)", 
         'postgresql://postgres.qagextokkrxrrmowyser:DataEko2026Secure!@aws-0-ap-south-1.pooler.supabase.com:6543/postgres'),
        ("Pooler-Session (port 5432)", 
         'postgresql://postgres.qagextokkrxrrmowyser:DataEko2026Secure!@aws-0-ap-south-1.pooler.supabase.com:5432/postgres'),
        ("Direct IPv4-forced", 
         'postgresql://postgres:DataEko2026Secure!@db.qagextokkrxrrmowyser.supabase.co:5432/postgres'),
    ]
    
    for label, url in tests:
        try:
            conn = await asyncpg.connect(url, timeout=10)
            res = await conn.fetch("SELECT current_user")
            print(f"✅ {label}: Connected as {res[0]['current_user']}")
            await conn.close()
        except Exception as e:
            print(f"❌ {label}: {type(e).__name__}: {e}")

asyncio.run(main())

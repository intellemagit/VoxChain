import os
import sys

# Add the project root to the python path so we can import intellema_vdk
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from intellema_vdk.retell_lib.retell_client import RetellManager

def import_twilio_number():
    """
    Import your Twilio phone number to Retell.
    This is required before you can make outbound calls using Retell.
    """
    try:
        manager = RetellManager()
        
        print("=== Retell Phone Number Import ===\n")
        print(f"Phone Number to import: {manager.twilio_number}")
        print(f"Agent ID to bind: {manager.retell_agent_id}\n")
        
        # Ask if user has a Twilio SIP trunk
        print("Do you have a Twilio Elastic SIP Trunk configured?")
        print("If you're not sure, you can:")
        print("  1. Visit: https://console.twilio.com/us1/develop/voice/manage/trunks")
        print("  2. Or just press Enter to try without it (may not work for some setups)\n")
        
        has_trunk = input("Do you have a SIP trunk? (y/n, default: n): ").strip().lower()
        
        termination_uri = None
        sip_username = None
        sip_password = None
        
        if has_trunk == 'y':
            print("\nEnter your Twilio SIP Trunk Termination URI.")
            print("Format: yourtrunkname.pstn.twilio.com")
            print("You can find this in Twilio Console > Elastic SIP Trunking > Your Trunk > Termination")
            termination_uri = input("Termination URI: ").strip()
            
            print("\nDo you use Credential List authentication? (Recommended)")
            has_creds = input("Use credentials? (y/n, default: y): ").strip().lower() or 'y'
            
            if has_creds == 'y':
                print("Enter the username/password from your Twilio Credential List:")
                sip_username = input("Username: ").strip()
                sip_password = input("Password: ").strip()
        
        # Optional nickname
        nickname = input("\nOptional: Enter a nickname for this number (press Enter to skip): ").strip() or None
        
        print(f"\n=== Importing Phone Number ===")
        
        response = manager.import_phone_number(
            termination_uri=termination_uri,
            nickname=nickname,
            sip_trunk_auth_username=sip_username,
            sip_trunk_auth_password=sip_password
        )
        
        print(f"\n=== Import Successful! ===")
        print(f"You can now use this number to make outbound calls via Retell.")
        
        return response
        
    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        print(f"\nTroubleshooting:")
        print(f"  1. If you don't have a SIP trunk, you may need to purchase the number through Retell")
        print(f"  2. Visit Retell dashboard: https://app.retellai.com/")
        print(f"  3. Or create a Twilio Elastic SIP Trunk first")
        raise

if __name__ == "__main__":
    import_twilio_number()

import time
from engine import build_and_deploy_fullstack_company

if __name__ == "__main__":
    print("=========================================================================")
    print("🌐 INFINITE AUTONOMOUS FULL-STACK FOUNDER SYSTEM READY")
    print("=========================================================================")
    
    while True:
        try:
            build_and_deploy_fullstack_company()
            print("\n⏰ Cooldown active. Next build sequence starts in 20 seconds...")
            time.sleep(20)
        except KeyboardInterrupt:
            print("\n🛑 Infinite Loop Engine paused safely. Enterprise state maintained.")
            break

"""
User entry point for DisectVal.
Default user version with standard permissions.
"""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def setup_logging():
    """Configure user mode logging."""
    if os.name == 'nt':
        log_dir = Path(os.environ.get('LOCALAPPDATA', '')) / 'DisectVal' / 'logs'
    else:
        log_dir = Path.home() / '.local' / 'share' / 'DisectVal' / 'logs'
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / 'user.log', encoding='utf-8'),
        ]
    )


def check_setup_complete() -> bool:
    """Check if initial setup has been completed."""
    if os.name == 'nt':
        base = Path(os.environ.get('LOCALAPPDATA', '')) / 'DisectVal'
    else:
        base = Path.home() / '.local' / 'share' / 'DisectVal'
    
    # Check for credential file existence
    cred_file = base / '.credentials.enc'
    return cred_file.exists()


def show_setup_required():
    """Show message that setup is required."""
    try:
        import customtkinter as ctk
        
        ctk.set_appearance_mode("dark")
        root = ctk.CTk()
        root.title("DisectVal - Setup Required")
        root.geometry("400x200")
        root.resizable(False, False)
        
        # Center
        root.update_idletasks()
        x = (root.winfo_screenwidth() - 400) // 2
        y = (root.winfo_screenheight() - 200) // 2
        root.geometry(f"400x200+{x}+{y}")
        
        ctk.CTkLabel(
            root,
            text="⚠️ Setup Required",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=20)
        
        ctk.CTkLabel(
            root,
            text="Please run Setup.exe first to initialize DisectVal.",
            wraplength=350
        ).pack(pady=10)
        
        ctk.CTkButton(
            root, text="OK", width=100,
            command=root.destroy
        ).pack(pady=20)
        
        root.mainloop()
        
    except ImportError:
        print("=" * 50)
        print("Setup Required")
        print("=" * 50)
        print("\nPlease run Setup.exe first to initialize DisectVal")
        print("and install required dependencies.")
        input("\nPress Enter to exit...")


def main():
    """Main user entry point."""
    setup_logging()
    logger.info("DisectVal User Mode starting")
    
    # Check if setup is complete
    if not check_setup_complete():
        logger.warning("Setup not complete")
        show_setup_required()
        sys.exit(0)
    
    # Launch the main application
    try:
        from disectval.main import DisectValApp
        
        app = DisectValApp()
        app.run()
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        print(f"\nError: {e}")
        print("\nPlease run Setup.exe to install dependencies.")
        input("Press Enter to exit...")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

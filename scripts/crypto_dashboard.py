import time
import sys

def main():
    try:
        while True:
            print("Fetching data...")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()

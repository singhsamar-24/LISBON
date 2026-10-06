from brain import LisbonBrain

def main():
    # Instantiate the butler brain
    butler = LisbonBrain()
    
    # Print the greeting
    print("\n" + "=" * 40)
    print(butler.get_greeting())
    print("=" * 40)
    
    # Print the system context Lisbon holds in memory
    print("\n[LISBON System Context Prompt]:")
    print(butler.build_system_prompt())
    print()

if __name__ == "__main__":
    main()

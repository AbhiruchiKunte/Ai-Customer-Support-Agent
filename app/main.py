import sys
from app.agent import SupportAgent

def run_agent():
    agent = SupportAgent(debug_mode=False)

    print("=" * 38)
    print("     Aster & Row Support Agent")
    print("=" * 38)
    print("Type 'exit' to quit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:
            response = agent.send_message(user_input)

            print("\nAgent:")
            print(response["answer"])

            if response["sources"]:
                print("\nSources:")
                for src in response["sources"]:
                    print(f"- Source: {src['filename']}")
                    print(f"  Section: {src['heading']}")

            if response["handoff"]:
                print("\n[HANDOFF RECOMMENDED] Recommending transfer to a human support agent.")

            print()

        except Exception as error:
            print("\nError:")
            print(error)
            print()

if __name__ == "__main__":
    run_agent()
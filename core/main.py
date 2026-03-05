from core.bootstrap import init_system


def main():

    print("Initializing Personal Music Architect...\n")

    app = init_system()

    print("System ready.")
    print("Type 'exit' to quit.\n")

    while True:

        user_input = input("You: ")

        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye.")
            break

        try:
            result = app.session.handle(user_input)

            message = result.get("clarification_message")

            if message:
                print(f"\nAgent: {message}\n")

            elif result.get("error"):
                print(f"\nError: {result['error']}\n")

            else:
                print("\nAgent: Request processed.\n")

        except Exception as e:
            print(f"\nSystem error: {e}\n")


if __name__ == "__main__":
    main()
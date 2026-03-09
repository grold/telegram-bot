import asyncio
import argparse
import sys
import logging
from tools.mock_aiogram import MockMessage, MockCommandObject, MockUser, MockBot

# Initialize logging
logging.basicConfig(level=logging.ERROR)

def main():
    parser = argparse.ArgumentParser(description="Telegram Bot CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # /start
    subparsers.add_parser("start", help="Welcome message")

    # /help
    subparsers.add_parser("help", help="Show help message")

    # /weather [city]
    weather_parser = subparsers.add_parser("weather", help="Get weather info")
    weather_parser.add_argument("city", nargs="?", help="City name")

    # /forecast [city]
    forecast_parser = subparsers.add_parser("forecast", help="Get weather forecast")
    forecast_parser.add_argument("city", nargs="?", help="City name")

    # /time [city]
    time_parser = subparsers.add_parser("time", help="Get local time")
    time_parser.add_argument("city", nargs="?", help="City name")

    # /top
    subparsers.add_parser("top", help="Show system resource usage")

    # /log [num] [query]
    log_parser = subparsers.add_parser("log", help="Show recent logs")
    log_parser.add_argument("num", nargs="?", default="10", help="Number of lines")
    log_parser.add_argument("query", nargs="*", help="Search query")

    # /camera [screenshot|video]
    camera_parser = subparsers.add_parser("camera", help="Camera controls")
    camera_parser.add_argument("action", choices=["screenshot", "video"], default="screenshot", nargs="?")
    camera_parser.add_argument("duration", nargs="?", help="Video duration")

    # /rate [pair]
    rate_parser = subparsers.add_parser("rate", help="Exchange rates")
    rate_parser.add_argument("pair", nargs="?", help="Currency pair (e.g. USD-EUR)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Run async command
    try:
        asyncio.run(execute_command(args))
    except KeyboardInterrupt:
        print("\nAborted.")
    except Exception as e:
        print(f"Error: {e}")

async def execute_command(args):
    # Initialize Database (needed for logs, rate limits, circle, etc.)
    from database import init_db
    init_db()

    # Create Mock Objects
    user = MockUser(username="cli_admin", id=777)
    bot = MockBot()
    message = MockMessage(from_user=user, bot=bot)

    if args.command == "start":
        from handlers.start import cmd_start
        await cmd_start(message)

    elif args.command == "help":
        from handlers.help import cmd_help
        await cmd_help(message)

    elif args.command == "weather":
        from handlers.weather import cmd_weather
        command_args = args.city
        command = MockCommandObject(args=command_args)
        await cmd_weather(message, command)

    elif args.command == "forecast":
        from handlers.forecast import cmd_forecast
        command_args = args.city
        command = MockCommandObject(args=command_args)
        await cmd_forecast(message, command)

    elif args.command == "time":
        from handlers.time import cmd_time
        command_args = args.city
        command = MockCommandObject(args=command_args)
        await cmd_time(message, command)

    elif args.command == "top":
        from handlers.top import cmd_top
        await cmd_top(message)

    elif args.command == "log":
        from handlers.log import cmd_log
        # Reconstruct args string for the handler
        command_args = f"{args.num}"
        if args.query:
            command_args += " " + " ".join(args.query)
        
        command = MockCommandObject(args=command_args)
        await cmd_log(message, command)

    elif args.command == "camera":
        from handlers.camera import cmd_camera
        command_args = args.action
        if args.action == "video" and args.duration:
            command_args += f" {args.duration}"
            
        command = MockCommandObject(args=command_args)
        await cmd_camera(message, command)

    elif args.command == "rate":
        from handlers.rate import cmd_rate
        command_args = args.pair
        command = MockCommandObject(args=command_args)
        await cmd_rate(message, command)

if __name__ == "__main__":
    main()

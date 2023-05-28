import argparse, logging
import aiohttp, asyncio

api = '/api/v9'
async def open_session(args):
    HEADERS = { 'Content-Type': 'application/json', 'Authorization': args.token }
    async with aiohttp.ClientSession('https://discord.com/', headers=HEADERS) as session:
        # Gather messages
        logging.info(f"Reading from file '{args.input}'")
        current_offset = 0
        with open(args.input, 'r') as inp:
            for line in inp:
                if current_offset >= args.offset:
                    line = line.strip().split('/')
                    logging.info(f'Deleting message at offset={current_offset}')
                    await delete_message(session, line[-2], line[-1])
                else:
                    if(args.verbose): logging.info(f'Skipping offset={current_offset}')
                current_offset += 1

        logging.info('No messages found!')

async def delete_message(session, channel_id, msg_id):
    async with session.delete(f"{api}/channels/{channel_id}/messages/{msg_id}") as resp:
        if resp.status == 404:
            logging.error('Message not found, skipping...')

        # Pause and retry if rate limited
        if resp.status == 429:
            sleep_for = int(resp.headers.get('Retry-After', 0))
            logging.error(f'We are being rate limited, retrying after {sleep_for}s...')
            await asyncio.sleep( sleep_for )
            await delete_message(session, channel_id, msg_id)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s | %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')    

    p = argparse.ArgumentParser()
    p.add_argument('token', type=str, help='discord token')
    p.add_argument('input', type=str, help='file name for list of message urls')
    p.add_argument('--offset', default=0, type=int, help='skip first n messages')
    p.add_argument('-v', '--verbose', action='store_true', help='verbose output')

    asyncio.run( open_session(p.parse_args()) )

import argparse, logging
import aiohttp, asyncio

api = '/api/v9'
async def open_session(args):
    HEADERS = { 'Content-Type': 'application/json', 'Authorization': args.token }
    async with aiohttp.ClientSession('https://discord.com/', headers=HEADERS) as session:
        # Get user information
        if not args.user: args.user = '@me'
        args.user = await get_user(session, args)

        # Gather messages
        file_name = f'messages_{args.user}_{args.guild}.txt' if args.output is None else args.output
        logging.info(f"Writing to file '{file_name}'")
        with open(file_name, 'a') as msglog:
            while True:
                # Tip: use offset flag and input whatever is printed here
                # to continue where you left off
                logging.info(f'Gathering messages with offset={args.offset}')

                bundle = await get_msgs(session, args.guild, args.user, args.offset)
                if(args.verbose): logging.info(bundle['messages'])

                # no more msgs to delete, exit loop
                if len(bundle['messages']) <= 0 or bundle['total_results'] <= 0: break

                # only gather messages sent by user
                msgs = (f"https://discord.com/channels/{args.guild}/{x[0]['channel_id']}/{x[0]['id']}" for x in bundle['messages'] if x[0]['author']['id'] == args.user)

                # write messages to file
                msglog.write('\n'.join(msgs) + '\n')

                # next page
                args.offset += 25

        logging.info('No more messages found!')

async def get_user(session, args):
    async with session.get(f'{api}/users/{args.user}') as resp:
        res = await resp.json()
        if(args.verbose): print(res)
        logging.info(f"Gathering messages from @{res['username']} in guild {args.guild}")
        return res['id']

async def get_msgs(session, guild_id, user_id, offset=0):
    # determine search parameters
    params = {'author_id': user_id, 'sort_by': 'timestamp', 'sort_order': 'asc', 'include_nsfw': 'true'}
    if offset > 0: params['offset'] = offset

    # GET bundle of messages
    async with session.get(f"{api}/guilds/{guild_id}/messages/search", params=params) as resp:
        res = await resp.json()

        # if rate limited, wait and recurse
        sleep_for = res.get('retry_after', 0)
        if sleep_for > 0:
            if(args.verbose): logging.error(f'We are being rate limited. Sleeping for {sleep_for}s...')
            await asyncio.sleep( sleep_for )
            return await get_msgs(session, guild_id, user_id, offset)

        return res

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s | %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')    

    p = argparse.ArgumentParser()
    p.add_argument('token', type=str, help='discord token')
    p.add_argument('guild', type=int, help='guild id')
    p.add_argument('-u', '--user', type=int, help='user id (default is self)')
    p.add_argument('--offset', default=0, type=int, help='skip first n messages')
    p.add_argument('-o', '--output', type=str, help='file name for output')
    p.add_argument('-v', '--verbose', action='store_true', help='verbose output')

    asyncio.run( open_session(p.parse_args()) )

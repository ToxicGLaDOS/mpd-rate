#!/usr/bin/env python3

from mpd import MPDClient
import sys
import subprocess
import traceback
import configparser
import os.path
import stat

def connect_to_server():
    client = MPDClient()
    if not os.path.isfile('mpd_config.ini'):
        raise Exception('No config file found.')
    st = os.stat('mpd_config.ini')
    if bool(st.st_mode & stat.S_IROTH) or bool(st.st_mode & stat.S_IWOTH) or bool(st.st_mode & stat.S_IXOTH):
        raise Exception('Config file has too loose of permissions. Make sure the other group has no permissions on mpd_confg.ini')
    config = configparser.ConfigParser()
    config.read('mpd_config.ini')
    client.timeout = 10
    client.idletimeout = None
    client.connect(config['auth']['hostname'], config['auth']['port'])
    client.password(config['auth']['password'])
    return client

def disconnect_from_server(client):
    client.close()
    client.disconnect()

def send_os_notification(summary, message):
    print(message)
    subprocess.Popen(['dunstify', '-t', '2000', summary, message])

def set_rating(client, uri, rating):
    client.sticker_set('song', uri, 'rating', rating)
    print('set rating')

def get_rating(client, uri):
    stickers = client.sticker_list('song', uri)
    if 'rating' in stickers.keys():
        return client.sticker_get('song', uri, 'rating')
    else:
        return 'No Rating Yet :('


def main():
    if len(sys.argv) > 2:
        # Subtract one for the implicit argument that's passed in
        print(f'Must have exactly zero or one argments, got: {len(sys.argv) - 1}')
        exit(1)

    if len(sys.argv) >= 2:
        rating = sys.argv[1]
        if rating not in [str(x) for x in range(1,11)]:
            print(f'First argument must be value between 1-10, got: {rating}')
            exit(1)
    else:
        rating = None


    client = connect_to_server()


    current_song_info = client.currentsong()
    if not current_song_info:
        raise Exception('No song currently playing')
    current_file = current_song_info['file']

    if rating:
        set_rating(client, current_file, rating)
        send_os_notification('Rating applied!', f"""Artist: {current_song_info['artist']}
Title: {current_song_info['title']}
Rating: {get_rating(client, current_file)}""")
    else:
        send_os_notification('Current rating:', f"""Artist: {current_song_info['artist']}
Title: {current_song_info['title']}
Rating: {get_rating(client, current_file)}""")

    disconnect_from_server(client)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        send_os_notification('ERROR:', str(e))
        traceback.print_exc()

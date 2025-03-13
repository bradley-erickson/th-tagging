import os
from dotenv import load_dotenv
import pickle
from pokemontcgsdk import Card, Set, RestClient

load_dotenv()

RestClient.configure(os.environ['POKEMONTCG_IO_API_KEY'])


def get_cards_by_series(series_name):
    print('Fetching cards by series')
    # Get all sets in the specified series
    sets_in_series = Set.where(q=f'series:"{series_name}"')
    
    all_cards = []
    for card_set in sets_in_series:
        print(' - Processing ', card_set.name)
        # Retrieve all cards from the current set
        cards_in_set = Card.where(q=f'set.id:"{card_set.id}"')
        all_cards.extend(cards_in_set)
    
    return all_cards


scarlet_violet = 'Scarlet & Violet'
card_file = '.sv_cards.bin'


if os.path.isfile(card_file):
  # Load cards from cached binary file if they exist
  with open(card_file, 'rb') as f:
    cards = pickle.load(f)
else:
  # Get cards from the API if the cache file is missing
    cards = get_cards_by_series(scarlet_violet)
    with open(card_file, 'wb') as f:
        pickle.dump(cards, f)


if __name__ == '__main__':
    print(Set.all())

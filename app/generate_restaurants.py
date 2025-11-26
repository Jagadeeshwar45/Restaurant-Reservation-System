import json
import random
from pathlib import Path
from faker import Faker

fake = Faker()
CUISINES = ['Indian','Italian','Chinese','Mexican','Mediterranean','Japanese','French','American','Thai','Korean']

def gen_restaurant(i):
    name = f"GoodFoods {fake.unique.last_name()}" if random.random()>0.3 else f"{fake.word().title()} Bistro"
    lat = 12.9 + random.random()*0.3
    lon = 77.45 + random.random()*0.3
    return {
        'id': i,
        'name': name,
        'address': fake.address().replace('\n', ', '),
        'lat': round(lat,6),
        'lon': round(lon,6),
        'capacity': random.choice([20,30,40,60,80,120,200]),
        'cuisine': random.choice(CUISINES),
        'features': random.sample(['outdoor','private_room','rooftop','live_music','parking','pet_friendly'], k=random.randint(0,2))
    }

if __name__ == '__main__':
    Path('../data').mkdir(parents=True, exist_ok=True)
    N = 80
    out = [gen_restaurant(i) for i in range(1, N+1)]
    with open('../data/restaurants.json','w',encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(out)} restaurants to data/restaurants.json")

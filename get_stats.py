
import sys


def b2i(data):
    return int.from_bytes(data, byteorder='little')

def parse_string(data, start = 0):
    index = start
    while data[index] != 0:
        index += 1
    
    end = index
    return data[start:end], end-start+1

class PlayerRecord:
    def __init__(self, data, start = 0, customgame = True):
        self.record_id = data[start]
        self.slot_record = None
        self.slot_order = None
        self.player_id = data[start+1]
        self.name, size = parse_string(data, start+2)
        self.name = self.name.decode('utf-8')
        self.additional_data = data[start + 2 + size]
        self.size = 2 + size + 1 + self.additional_data
        """
        if customgame:
            #extra null byte
            self.size += 1    
        else:
            #runtime + race
            self.size += 8
        
        #sometimes extra nullbyte, only if it's the player?
        if data[start + self.size] == 0:
            self.size +=1
        """

    def __str__(self):
        return str((#self.record_id,
                    self.player_id, self.record_id, self.name, self.slot_order
        ))

def parse_players(data):
    
    # Start up items:
    index = 0x44 + 4
    hostplayer = PlayerRecord(data, index) 
    index += hostplayer.size
   
    gamename, size = parse_string(data, index)
    index += size

    index += 1 # nullbyte
    
    encoded_string, size = parse_string(data, index)
    index += size

    index += 4 #allocating player count, only for lobby? used to be 24 for bots.
    index += 4 #gametype
    index += 4 #languageID
    
    #Player list
    players = [hostplayer]
    while data[index] == 0x16:
        player = PlayerRecord(data, index)
        index += player.size
        players += [player]
        index += 4 # some reoccuring bytes
   
    #GameStartRecord (ignoring)
    assert data[index] == 0x19

    slotrecords, index, random_seed = parse_gamestartrecord(data, index)

    observers = []

    # Filtering out observers
    for slotrecord in slotrecords:
        for player in players:
            if player.player_id == slotrecord[0]:
                player.slot_record = slotrecord

            if slotrecord[3] == 24:
                if player.player_id == slotrecord[0]:
                    players.remove(player)
                    observers += [player]

    for n in range(len(players)):
        players[n].slot_order = n

    return players, observers


def parse_gamestartrecord(data, index=0):
    assert data[index] == 0x19
    index += 1
    length = b2i(data[index:index+2])
    index += 2
    nr_of_slotrecords = data[index]
    index += 1

    slotrecords = []
    for n in range(nr_of_slotrecords):
        pid = data[index]
        index += 1
        index += 1 #map DL status
        slotstatus = ['empty', 'closed', 'used'][data[index]]
        index += 1
        computer_player_flag = ['human', 'computer'][data[index]]
        index += 1
        team_number = data[index]
        index += 1
        color = data[index]
        index += 1
        player_race = data[index]
        index += 1
        comp_ai_strength = data[index]
        index += 1
        player_handicap = data[index]
        index += 1
        slotrecord = [pid, slotstatus, computer_player_flag,
                      team_number, color, player_race,
                      comp_ai_strength, player_handicap]
        slotrecords += [slotrecord]


    #index += 4 #rest stuff
    #index += 9
    random_seed = data[index:index+4]
    #print(byte_to_int(random_seed))
    index += 4
    select_mode = data[index]
    #print(hex(select_mode))
    index += 1
    start_spot_count = data[index]
    #print(hex(start_spot_count))
    index += 1
    assert data[index] == 0x1a  # start of replay data
    return slotrecords, index, random_seed


def parse_w3mmd(data, index = 0):
    w3mmd_data = []
    while index < len(data):
        index = data.find(b'kdr.x\x00', index)
        if index == -1:
            break
        else:
            index += len(b'kdr.x\00')

        w3mmd_type, size = parse_string(data, index)
        index += size
        w3mmd_key, size = parse_string(data, index)
        index += size
        w3mmd_value = data[index:index+4]
        index += 4
       
        w3mmd_data += [(w3mmd_type, w3mmd_key, w3mmd_value)]

    return w3mmd_data

def parse_civw3mmd(data, index=0):
    w3mmd_data = []
    while index < len(data):
        index = data.find(b'kMMD.', index)
        if index == -1:
            break
        else:
            index += len(b'kMMD.')
        w3mmd_type, size = parse_string(data, index)
        index += size
        w3mmd_key, size = parse_string(data, index)
        index += size
        w3mmd_value, size = parse_string(data, index)
        index += size

        w3mmd_data += [(w3mmd_key.decode('utf-8'), w3mmd_value.decode('utf-8'))]

    return w3mmd_data

def get_replay_length(data):
    return b2i(data[0x3C:0x3C+4])

if __name__ == '__main__':
    filename = sys.argv[1]
    #filename = 'latte_vs_brando_06.08.2019.txt'
    f = open(filename, "rb")
    data = f.read()
    f.close()
    
    f = open(filename[:-3]+'log', 'w')

    oldprint = print
    def print(text=""):
        oldprint(text, file=f)
        oldprint(text)

    players, observers = parse_players(data)

    print('players')
    for player in players:
        print(player)
    print('observers')
    for observer in observers:
        print(observer)

    w3mmd_data = parse_w3mmd(data)

    print("w3mmd:")
    for w3mmd in w3mmd_data:
        if w3mmd[1] in [b'Tree', b'Throne']:
            print(w3mmd)

    print(get_replay_length(data))

    f.close()

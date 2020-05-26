

# Делае число четным
def make_even(value):
    return (value // 2) * 2


# m/sec to km/h
def meters_per_second_to_kilometers_per_hour(value):
    return value * 3.6


# km/h to m/sec
def kilometers_per_hour_to_meters_per_second(value):
    return value / 3.6


# m/sec to turn/min
def meters_per_second_to_turns_per_minute(value, one_turn_distance):
    return value * 60 / one_turn_distance


# turn/min to m/sec
def turns_per_minute_to_meters_per_second(value, one_turn_distance):
    return turns_per_minute_to_kilometers_per_hour(value, one_turn_distance) / 3.6


# turn/min to km/h
def turns_per_minute_to_kilometers_per_hour(value, one_turn_distance):
    return value * 60 * (one_turn_distance / 1000)


# km/h to turn/min
def kilometers_per_hour_to_turns_per_minute(value, one_turn_distance):
    return value / 60 / (one_turn_distance / 1000)




from players.models import SquadStructure

positions_names = {0: ['Point Guard'], 1: ['Shooting Guard', 'Combo Guard'], 2: ['Combo Guard'],
                   3: ['Stretch Big', 'Power Forward', 'Wing'], 4: ['Stretch Big', 'Center']}


def validate_squad_structure(structure, players, user):
    structure_position = dict(SquadStructure.structure_position)
    players_positions = {
        player: str(player.player_profile.position.name).lower().replace(" ", "")
        for player in players
    }
    players_positions[user] = str(user.player_profile.position.name).lower().replace(" ", "")

    # print(players_positions)

    def get_payer(player_pos: str):
        for i in players_positions:
            if players_positions[i] == player_pos:
                del players_positions[i]
                return i  # player
        return False

    structure = {
        0: [str(structure_position[p]).lower().replace(" ", "") for p in structure.position_1],
        1: [str(structure_position[p]).lower().replace(" ", "") for p in structure.position_2],
        2: [str(structure_position[p]).lower().replace(" ", "") for p in structure.position_3],
        3: [str(structure_position[p]).lower().replace(" ", "") for p in structure.position_4],
        4: [str(structure_position[p]).lower().replace(" ", "") for p in structure.position_5]
    }

    # arrange players
    structured_players = []
    for struc in structure:
        position_length = len(structure[struc])

        for index, position in enumerate(structure[struc]):
            player = get_payer(position)
            if player:
                structured_players.append(
                    player
                )
                # del players_positions[position]
                break
            else:
                # print(f"position {struc+1} -- {position_length} --- {structure[struc]}")
                # if position_length > 1:
                #     continue
                if index + 1 < position_length:
                    continue
                return False, [
                    f"Please add player with {positions_names[struc]}." if len(
                        positions_names[struc]) > 1
                    else f"{positions_names[struc][0]} player should be required."
                ]
    return True, structured_players

# def validate_squad_structure1(structure, players, user):
#     structure_position = dict(SquadStructure.structure_position)
#
#     structure = {
#         0: [str(structure_position[p]).lower().replace(" ", "") for p in structure.position_1],
#         1: [str(structure_position[p]).lower().replace(" ", "") for p in structure.position_2],
#         2: [str(structure_position[p]).lower().replace(" ", "") for p in structure.position_3],
#         3: [str(structure_position[p]).lower().replace(" ", "") for p in structure.position_4],
#         4: [str(structure_position[p]).lower().replace(" ", "") for p in structure.position_5]
#     }
#
#     # current player
#     player_position = user.player_profile.position
#     all_positions = [pos for sublist in structure.values() for pos in sublist]
#     print(player_position)
#
#     if str(player_position).lower().replace(" ", "") not in all_positions:
#         return False, f"your position {player_position} not match to this structure."
#
#     # others players
#     for index, player in enumerate(players):
#         player_position = player.player_profile.position
#         if str(player_position).lower().replace(" ", "") not in structure[index]:
#             return False, [
#                 f"invalid player position at {index + 1}. {player_position}",
#                 f"it should be '{structure[index]}'."
#             ]
#     return True, True

from room import Room
from player import Player
from world import World

import random
from ast import literal_eval
from util import Queue, Stack

import multiprocessing

# Load world
world = World()


# You may uncomment the smaller graphs for development and testing purposes.
# map_file = "maps/test_line.txt"
# map_file = "maps/test_cross.txt"
# map_file = "maps/test_loop.txt"
# map_file = "maps/test_loop_fork.txt"
map_file = "maps/main_maze.txt"

# Loads the map into a dictionary
room_graph = literal_eval(open(map_file, "r").read())
world.load_graph(room_graph)

# Print an ASCII map
# world.print_rooms()

player = Player(world.starting_room)

# * START
"""
Goal: 
    Traverse a maze of 500 rooms such that the steps taken to visit
    all of them take less than 2000 moves
Stretch: 
    Do it under 959 steps

Traverse a maze of 500 rooms that contain cycles (undirected cyclic graph)
Each room has between 0-4 exits "N,S,W,E"
Each room has an id that we can get using room.id.
Each room has exits that we can get using room.get_exits()

Access current room info using player.current_room 
To traverse our maze we use player.travel(string direction) - valid directions ("n", "s", "w", "e")

Thoughts
a var to hold visited rooms must exist

instead of adding data to mark what paths we took between rooms, just delete the path choice

when I move in d direction, I need to keep track of my reverse path so I can backtrack later at a dead end
when a dead end is reached I need to walk back to previous room and see if I can go a different path from there

3 cases to handle
Picking a room and travelling ( Picking a new direction from a visited room )
Finding an unvisited room ( Build exits, append to path)
Reaching a dead end room ( Backtrack from here)

If room not visited
    add room and its exits to traversal path / visited dict
    remove "exit" where we just came from (opposite direction travelled)
If room has no exits
    backtrack to previous room
    Add step to path
room IS visited (built and ready)
    pick direction to travel
    add opposite dir to reversed path list
    remove direction from room so we don't go thru it again
    add step to path
"""
# DEBUG
# print(player.current_room.id)
# print(player.current_room.get_exits())
# print(player.travel("n"))
def traverse_maze(test=True):
    # Holds our end NSWE steps journey
    traversal_path = []
    # Reverse of traversal_path
    reversed_traversal_path = []
    # Dict for rooms visited
    visited = {}

    # Handy dict for getting opposite direction just travelled
    from_dir = {"n": "s", "s": "n", "w": "e", "e": "w"}

    # Build starting room and exits
    visited[player.current_room.id] = player.current_room.get_exits()

    # We know were done when we have visited all rooms in room_graph
    while len(visited) < len(room_graph):

        # Unvisited room case
        if player.current_room.id not in visited:
            # Get room exits
            exits = player.current_room.get_exits()
            # Remove the path we just came from (direction is reversed)
            exits.remove(from_dir[traversal_path[-1]])
            # Add room and exits to visited
            visited[player.current_room.id] = exits

        # Dead end / no more paths case
        # Need to backtrack from here to previous room
        if len(visited[player.current_room.id]) == 0:
            # Since we are going back to previous room,
            # we need to add this action as a step in the
            # traversal path
            # Get last step
            last_step_direction = reversed_traversal_path.pop()

            # Add to our path
            traversal_path.append(last_step_direction)
            # Move player to previous room
            player.travel(last_step_direction)

        else:
            # Pick last available direction
            direction_choices = len(visited[player.current_room.id])
            direction_index = (
                random.randint(0, direction_choices - 1) if direction_choices > 0 else 0
            )
            direction = visited[player.current_room.id][direction_index]
            # Remove from choices so we don't travel down this path again
            visited[player.current_room.id].pop(direction_index)
            # Move player to next room
            player.travel(direction)
            # Add to path tracker
            traversal_path.append(direction)
            # Add inverse of direction to reversed_path
            reversed_traversal_path.append(from_dir[direction])
    if test:
        return traversal_path
    else:
        return len(traversal_path)


def thread_find_lowest_steps(worker, iterations, progress_step, work_result):
    step_container = []
    percent_complete = 0
    progress_print_at_value = iterations * (progress_step / 100)

    print("Starting run...")

    for i in range(0, iterations):
        # Print progress at each progress_step
        if i != 0 and i % progress_print_at_value == 0:
            percent_complete += progress_step

            # Get current minimum
            min_so_far = min(step_container)
            # Dump old runs
            step_container.clear()
            # Add calculated min
            step_container.append(min_so_far)

            print(
                f"Worker: {worker} Progress... {percent_complete}% Shortest traversal so far: {min_so_far}"
            )
        # Traverse maze and append result to steps
        step_container.append(traverse_maze(False))

    # Get final min
    shortest_traversal = min(step_container)

    print("\n...Run complete")
    print("Lowest steps to solve: ", shortest_traversal)

    work_result[worker] = shortest_traversal


def find_lowest_steps(iterations, step, use_all_cores=False):

    if use_all_cores:
        # List to hold our child processes
        processes = []
        # Core count of this machine
        cpu_count = multiprocessing.cpu_count() - 1
        # Setup shared array so we can get the final result of each process
        work_result = multiprocessing.Array("i", cpu_count)

        for i in range(0, cpu_count):
            # Create process
            child_process = multiprocessing.Process(
                target=thread_find_lowest_steps,
                args=(i, iterations, step, work_result,),
            )
            # Start working
            child_process.start()
            # Print PID of new worker
            print(f"Worker {i} started with pid of {child_process.pid}")
            # Add to tracking list
            processes.append(child_process)

        # Join them all back to the main process here
        for process in processes:
            process.join()

        # Print minimum path found out of all workers
        print("\n\n...Shortest traversal out of all workers: ", min(work_result))

    else:
        thread_find_lowest_steps(0, iterations, step, [None])


def traversal_test():
    # TRAVERSAL TEST
    visited_rooms = set()
    traversal_path = traverse_maze()
    player.current_room = world.starting_room
    visited_rooms.add(player.current_room)

    for move in traversal_path:
        player.travel(move)
        visited_rooms.add(player.current_room)

    if len(visited_rooms) == len(room_graph):
        print(
            f"TESTS PASSED: {len(traversal_path)} moves, {len(visited_rooms)} rooms visited"
        )
    else:
        print("TESTS FAILED: INCOMPLETE TRAVERSAL")
        print(f"{len(room_graph) - len(visited_rooms)} unvisited rooms")


if __name__ == "__main__":
    # ************************************************#
    # ORIGINAL TEST DRIVER CODE
    # traversal_test()

    # ************************************************#
    # FIND LOWEST STEP IN X ITERATIONS
    iterations = 5000  # How many tries to we want to do
    percent_notify = 10  # Print progress at N percent (1-100)
    # Will only use cpu core count - 1 if use_all_cores is True
    # Otherwise it will only run on the main thread
    find_lowest_steps(iterations=iterations, step=percent_notify, use_all_cores=False)

    # Shortest steps recorded: 972

    #######
    # UNCOMMENT TO WALK AROUND
    #######
    # player.current_room.print_room_description(player)
    # while True:
    #     cmds = input("-> ").lower().split(" ")
    #     if cmds[0] in ["n", "s", "e", "w"]:
    #         player.travel(cmds[0], True)
    #     elif cmds[0] == "q":
    #         break
    #     else:
    #         print("I did not understand that command.")

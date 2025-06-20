import votekit.ballot_generator as bg
from votekit.pref_interval import PreferenceInterval
import votekit.elections as elec
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt

from collections import Counter


def simulate_party_list_election(
    bloc_voter_prop, cohesion_parameters, n_ballots=1000, num_seats=5
):
    blocs = list(bloc_voter_prop.keys())
    parties = list(next(iter(cohesion_parameters.values())).keys())  # All parties

    # Step 1: Generate ballots
    bloc_choices = np.random.choice(
        blocs, size=n_ballots, p=[bloc_voter_prop[b] for b in blocs]
    )
    ballots = []

    for bloc in bloc_choices:
        party_probs = [cohesion_parameters[bloc][party] for party in parties]
        voted_party = np.random.choice(parties, p=party_probs)
        ballots.append(voted_party)

    # Step 2: Tally votes
    vote_counts = Counter(ballots)

    # Step 3: Allocate seats proportionally using Largest Remainder (Hare quota)
    total_votes = sum(vote_counts.values())
    quota = total_votes / num_seats

    initial_allocations = {
        party: int(vote_counts.get(party, 0) // quota) for party in parties
    }
    remainder = {party: vote_counts.get(party, 0) % quota for party in parties}

    # Remaining seats to assign after initial quotas
    allocated = sum(initial_allocations.values())
    seats_remaining = num_seats - allocated

    # Assign remainder seats to highest remainders
    remainder_sorted = sorted(remainder.items(), key=lambda x: -x[1])
    for i in range(seats_remaining):
        initial_allocations[remainder_sorted[i][0]] += 1

    return initial_allocations  # Dict with party: seats


slate_to_candidates = {
    "R": ["R1", "R2"],
    "D": ["D1", "D2", "D3", "D4", "D5", "D6", "D7"],
    "P": ["P1", "P2", "P3", "P4"],
}

# note that we include candidates with 0 support,
# and that our preference intervals will automatically rescale to sum to 1

pref_intervals_by_bloc = {
    "R": {
        "R": PreferenceInterval({"R1": 0.2, "R2": 0.8}),
        "D": PreferenceInterval(
            {
                "D1": 0.1,
                "D2": 0.1,
                "D3": 0.1,
                "D4": 0.1,
                "D5": 0.4,
                "D6": 0.1,
                "D7": 0.1,
            }
        ),
        "P": PreferenceInterval({"P1": 0.5, "P2": 0.3, "P3": 0.1, "P4": 0.1}),
    },
    "D": {
        "R": PreferenceInterval({"R1": 0.5, "R2": 0.5}),
        "D": PreferenceInterval(
            {
                "D1": 0.3,
                "D2": 0.2,
                "D3": 0.1,
                "D4": 0.1,
                "D5": 0.1,
                "D6": 0.1,
                "D7": 0.1,
            }
        ),
        "P": PreferenceInterval({"P1": 0.5, "P2": 0.3, "P3": 0.1, "P4": 0.1}),
    },
    "P": {
        "R": PreferenceInterval({"R1": 0.8, "R2": 0.2}),
        "D": PreferenceInterval(
            {
                "D1": 0.1,
                "D2": 0.1,
                "D3": 0.2,
                "D4": 0.2,
                "D5": 0.2,
                "D6": 0.1,
                "D7": 0.1,
            }
        ),
        "P": PreferenceInterval({"P1": 0.5, "P2": 0.3, "P3": 0.1, "P4": 0.1}),
    },
}


bloc_voter_prop = {"R": 0.2, "D": 0.4, "P": 0.4}


# assume that each bloc is 90% cohesive
# we'll discuss exactly what that means later
def make_cohesion(p_to_d, d_to_p, d_to_r, r_to_d):
    return {
        "D": {
            "R": d_to_r,
            "D": 1 - d_to_r - d_to_p,
            "P": d_to_p,
        },
        "R": {"R": 1 - r_to_d, "D": r_to_d, "P": 0},
        "P": {"R": 0, "D": p_to_d, "P": 1 - p_to_d},
    }


def tally_results(result):
    result_dict = {"R": 0, "D": 0, "P": 0}
    for entry in result:
        result_dict[list(entry)[0][0]] += 1
    return result_dict


stv_results = {}
pl_results = {}
n_simulations = 10

d_to_x = np.linspace(0, 0.5, 21)
x_to_d = np.linspace(0, 0.5, 21)
# Total iterations: outer grid (11x11) × simulations
total_iters = len(d_to_x) * len(x_to_d) * n_simulations
pbar = tqdm(total=total_iters)

for i, d_to_x_ in tqdm(enumerate(d_to_x), total=len(d_to_x)):
    stv_results[d_to_x_] = {}
    pl_results[d_to_x_] = {}

    for j, x_to_d_ in enumerate(x_to_d):
        cumulative_result_stv = {"R": 0, "D": 0, "P": 0}
        cumulative_result_partylist = {"R": 0, "D": 0, "P": 0}

        for _ in range(n_simulations):
            p_to_d = x_to_d_
            d_to_p = d_to_x_
            d_to_r = d_to_x_
            r_to_d = x_to_d_

            cohesion_parameters = make_cohesion(
                p_to_d=p_to_d, d_to_p=d_to_p, d_to_r=d_to_r, r_to_d=r_to_d
            )

            # --- Party List ---
            partylist_result = simulate_party_list_election(
                bloc_voter_prop=bloc_voter_prop,
                cohesion_parameters=cohesion_parameters,
                n_ballots=1000,
                num_seats=5,
            )
            for key in cumulative_result_partylist:
                cumulative_result_partylist[key] += partylist_result.get(key, 0)

            # --- STV ---
            pl = bg.slate_PlackettLuce(
                pref_intervals_by_bloc=pref_intervals_by_bloc,
                bloc_voter_prop=bloc_voter_prop,
                slate_to_candidates=slate_to_candidates,
                cohesion_parameters=cohesion_parameters,
            )
            profile = pl.generate_profile(number_of_ballots=1000)
            election = elec.STV(profile, m=5)
            sim_result = tally_results(election.get_elected())
            for key in cumulative_result_stv:
                cumulative_result_stv[key] += sim_result.get(key, 0)

            pbar.update(1)
        stv_results[d_to_x_][x_to_d_] = cumulative_result_stv
        pl_results[d_to_x_][x_to_d_] = cumulative_result_partylist

# create matrix of results
R_matrix = np.zeros((len(d_to_x), len(x_to_d)))
D_matrix = np.zeros((len(d_to_x), len(x_to_d)))
P_matrix = np.zeros((len(d_to_x), len(x_to_d)))

for i, d_to_x_ in enumerate(d_to_x):
    for j, x_to_d_ in enumerate(x_to_d):
        counts = stv_results[d_to_x_][x_to_d_]
        R_matrix[i, j] = counts["R"] / n_simulations
        D_matrix[i, j] = counts["D"] / n_simulations
        P_matrix[i, j] = counts["P"] / n_simulations


R_matrix_pl = np.zeros((len(d_to_x), len(x_to_d)))
D_matrix_pl = np.zeros((len(d_to_x), len(x_to_d)))
P_matrix_pl = np.zeros((len(d_to_x), len(x_to_d)))

for i, d_to_x_ in enumerate(d_to_x):
    for j, x_to_d_ in enumerate(x_to_d):
        counts = pl_results[d_to_x_][x_to_d_]
        R_matrix_pl[i, j] = counts["R"] / n_simulations
        D_matrix_pl[i, j] = counts["D"] / n_simulations
        P_matrix_pl[i, j] = counts["P"] / n_simulations


fig = plt.figure(figsize=[8, 8])
plt.imshow(
    D_matrix.T,
    origin="lower",
    extent=[d_to_x[0], d_to_x[-1], x_to_d[0], x_to_d[-1]],
    cmap="inferno",
    vmin=0,
    vmax=5,
)
plt.xlabel("Democrat outflow rate")
plt.ylabel("Democrat inflow rate")
plt.colorbar()
plt.show()

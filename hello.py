import votekit.ballot_generator as bg
from votekit.pref_interval import PreferenceInterval
import votekit.elections as elec

slate_to_candidates = {
    "Republican": ["R1", "R2"],
    "Democrat": ["D1", "D2", "D3", "D4", "D5", "D6", "D7"],
    "Progressive": ["P1", "P2", "P3", "P4"],
}

# note that we include candidates with 0 support,
# and that our preference intervals will automatically rescale to sum to 1

pref_intervals_by_bloc = {
    "Republican": {
        "Republican": PreferenceInterval({"R1": 0.2, "R2": 0.8}),
        "Democrat": PreferenceInterval(
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
        "Progressive": PreferenceInterval({"P1": 0.5, "P2": 0.3, "P3": 0.1, "P4": 0.1}),
    },
    "Democrat": {
        "Republican": PreferenceInterval({"R1": 0.5, "R2": 0.5}),
        "Democrat": PreferenceInterval(
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
        "Progressive": PreferenceInterval({"P1": 0.5, "P2": 0.3, "P3": 0.1, "P4": 0.1}),
    },
    "Progressive": {
        "Republican": PreferenceInterval({"R1": 0.8, "R2": 0.2}),
        "Democrat": PreferenceInterval(
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
        "Progressive": PreferenceInterval({"P1": 0.5, "P2": 0.3, "P3": 0.1, "P4": 0.1}),
    },
}


bloc_voter_prop = {"Republican": 0.2, "Democrat": 0.4, "Progressive": 0.4}


# assume that each bloc is 90% cohesive
# we'll discuss exactly what that means later
def make_cohesion(p_to_d, d_to_p, d_to_r, r_to_d):
    return {
        "Democrat": {
            "Republican": d_to_r,
            "Democrat": 1 - d_to_r - d_to_p,
            "Progressive": d_to_p,
        },
        "Republican": {"Republican": 1 - r_to_d, "Democrat": r_to_d, "Progressive": 0},
        "Progressive": {"Republican": 0, "Democrat": p_to_d, "Progressive": 1 - p_to_d},
    }


# TO DO : do this as a loop instead of a 1-off
cohesion_parameters = make_cohesion(0.2, 0.2, 0.2, 0.2)

pl = bg.slate_PlackettLuce(
    pref_intervals_by_bloc=pref_intervals_by_bloc,
    bloc_voter_prop=bloc_voter_prop,
    slate_to_candidates=slate_to_candidates,
    cohesion_parameters=cohesion_parameters,
)

profile = pl.generate_profile(number_of_ballots=1000)

election = elec.STV(profile, m=5)

election.get_elected()

from qseries_v2.oi.probability_engine import probability_engine

confidence = 91.67

prob = probability_engine.probability(confidence)
yes = probability_engine.fair_yes_price(confidence)
no = probability_engine.fair_no_price(confidence)
edge = probability_engine.expected_edge(85, yes)

assert round(prob,2) == 0.92
assert yes > no
assert edge > 0

print("[PASS] OI-003 Probability Engine")
print(f"Probability : {prob:.4f}")
print(f"Fair YES    : {yes}")
print(f"Fair NO     : {no}")
print(f"Edge        : {edge}")

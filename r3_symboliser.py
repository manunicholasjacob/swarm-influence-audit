"""Does the result depend on how we turned language into symbols?

The report's biggest declared limitation is that symbolisation is a free parameter. The headline used
TF-IDF then k-means. This re-runs the two decisive channels with a different symboliser (TF-IDF then
latent semantic analysis, then k-means) under both surrogates. If the pattern holds, the conclusion is
about the surrogate rather than about one clustering choice.
"""
import json, time
import numpy as np
import swarmlib as S
from swarm_load import normalise, SILENT

GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
K, N, TOP_K = 8, 200, 15
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)


class LSASymboliser:
    """TF-IDF -> truncated SVD (latent semantic analysis) -> k-means. A different route to topics."""
    def __init__(self, k=8, seed=0, n_components=50):
        self.k, self.seed, self.n_components = k, seed, n_components
        self._vec = self._svd = self._km = None

    def fit(self, texts):
        from sklearn.cluster import KMeans
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
        corpus = [normalise(t) for t in texts]
        keep = [c for c in corpus if c]
        self._vec = TfidfVectorizer(min_df=2, max_features=20000)
        x = self._vec.fit_transform(keep)
        comp = min(self.n_components, max(2, x.shape[1] - 1))
        self._svd = TruncatedSVD(n_components=comp, random_state=self.seed)
        z = self._svd.fit_transform(x)
        self._km = KMeans(n_clusters=self.k, random_state=self.seed, n_init=10).fit(z)
        return self

    def transform(self, texts):
        corpus = [normalise(t) for t in texts]
        idx = [i for i, c in enumerate(corpus) if c]
        out = [SILENT]*len(corpus)
        if idx:
            z = self._svd.transform(self._vec.transform([corpus[i] for i in idx]))
            for i, lab in zip(idx, self._km.predict(z)):
                out[i] = "L%d" % lab
        return out


def run_channel(village, label):
    msgs, names, rooms = S.load_village(village)
    room = GENERAL if village == "main-village" else S.busiest_room(msgs)
    span, lo, hi = S.cut_window(msgs, room, days=14)
    texts = [m["content"] for m in span]
    lsa = LSASymboliser(k=K, seed=0).fit(texts)
    for m, s in zip(span, lsa.transform(texts)):
        m["_lsa"] = s
    S.symbolise(span, k=K, seed=0)          # also attaches _topic and _hash for comparison
    agents = S.select_agents(span, min_msgs=50, top_k=TOP_K)
    rec = {"village": village, "window_msgs": len(span), "agents": len(agents)}
    for key, name in (("_topic", "tfidf_kmeans"), ("_lsa", "lsa_kmeans"), ("_hash", "hash")):
        rec[name] = {}
        for null in ("shift", "permute"):
            _, e, n = S.run_window(span, agents, key=key, n_shifts=N, null=null)
            rec[name][null] = len(e)
            rec["n_ticks"] = n
        log(f"{label} {name:14s}: shift {rec[name]['shift']:3d} | permute {rec[name]['permute']:3d}")
    return rec

out = {"k": K, "n_surrogates": N, "channels": []}
for v, lab in (("main-village", "main"), ("open-chat-village", "open-chat")):
    out["channels"].append(run_channel(v, lab))
    json.dump(out, open("facts_symboliser.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_symboliser.json")

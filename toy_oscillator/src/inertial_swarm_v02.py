#!/usr/bin/env python3
"""Chimera-Live reference experiment: hierarchical inertial phase oscillators.

Reproducible numerical toy-model ONLY. This is NOT a LLM experiment, an
established Chimera state, a genuine dynamical hysteresis proof, or a
measurement of collective goal drift.
"""
import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def order_parameter(theta):
    return float(np.abs(np.exp(1j * theta).mean()))


def setup(seed, n_groups, n_per_group, omega_std):
    rng = np.random.default_rng(seed)
    n = n_groups * n_per_group
    groups = np.repeat(np.arange(n_groups), n_per_group)
    theta = rng.uniform(-np.pi, np.pi, n)
    omega = rng.normal(0, omega_std, n)
    omega -= omega.mean()
    v = omega.copy()
    h = np.zeros(n_groups)
    # Row-normalized intra- and inter-group coupling. No self-links.
    same = groups[:, None] == groups[None, :]
    wi = (same & ~np.eye(n, dtype=bool)).astype(float)
    wo = (~same).astype(float)
    wi /= np.maximum(wi.sum(axis=1, keepdims=True), 1.)
    wo /= np.maximum(wo.sum(axis=1, keepdims=True), 1.)
    return groups, theta, omega, v, h, wi, wo


def simulate(seed, memory_feedback, plateau, dt, k_max, nk, n_groups=3, n_per_group=8,
             inertia=1.3, damping=0.7, omega_std=0.75, out_ratio=0.16,
             alpha_in=0.10, alpha_out=0.25, tau_h=24.0,
             memory_gain=0.85, threshold=0.8):
    groups, theta, omega, v, h, wi, wo = setup(seed, n_groups, n_per_group, omega_std)
    kpath = np.concatenate([np.linspace(0, k_max, nk), np.linspace(k_max, 0, nk)[1:]])
    nsteps = int(round(plateau / dt))
    if nsteps < 2:
        raise ValueError('plateau / dt must be >= 2')
    records = []
    recovery = []
    total_step = 0
    for pi, kbase in enumerate(kpath):
        phase = 'up' if pi < nk else 'down'
        for j in range(nsteps):
            z = np.array([order_parameter(theta[groups == g]) for g in range(n_groups)])
            h += (dt / tau_h) * (z - h)
            # Historical residual H is measured for both conditions; only enabled
            # feedback changes the effective coupling, not the scoring rule.
            gains = 1.0 + (memory_gain * h[groups] if memory_feedback else 0.0)
            delta = theta[None, :] - theta[:, None]
            intra = (wi * np.sin(delta - alpha_in)).sum(axis=1)
            inter = (wo * np.sin(delta - alpha_out)).sum(axis=1)
            acceleration = (damping * (omega - v) +
                            kbase * gains * intra + out_ratio * kbase * inter) / inertia
            v += dt * acceleration
            theta = (theta + dt * v + np.pi) % (2*np.pi) - np.pi
            total_step += 1
            if j % max(1, nsteps // 50) == 0:
                recovery.append(dict(t=total_step*dt, K=float(kbase), phase=phase,
                                     R_mean=float(z.mean()), R_global=order_parameter(theta),
                                     H_mean=float(h.mean()),
                                     memory_feedback=bool(memory_feedback), seed=seed))
        # Only terminal portion of each plateau is used as the quasi-stationary
        # diagnostic; no claim that this is an equilibrium.
        z = np.array([order_parameter(theta[groups == g]) for g in range(n_groups)])
        records.append(dict(seed=seed, memory_feedback=bool(memory_feedback),
                            phase=phase, K=float(kbase), R_mean=float(z.mean()),
                            R_min=float(z.min()), R_max=float(z.max()),
                            R_global=order_parameter(theta), H_mean=float(h.mean()),
                            groups_above_08=int((z > threshold).sum())))
    return records, recovery


def save_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


def make_figures(out, records, traces):
    for mem in (False, True):
        fig, ax = plt.subplots(figsize=(8, 4.8))
        for phase, linestyle in [('up', '-'), ('down', '--')]:
            rr = [r for r in records if r['seed'] == records[0]['seed']
                  and r['memory_feedback'] == mem and r['phase'] == phase]
            ax.plot([r['K'] for r in rr], [r['R_mean'] for r in rr],
                    linestyle=linestyle, marker='o', markersize=3, label=phase)
        ax.set(xlabel='Nominal coupling K', ylabel='Mean within-harness coherence R',
               title=f"Finite-rate up/down sweep ({'H feedback' if mem else 'No H feedback'})",
               ylim=(0, 1.05))
        ax.legend(); fig.tight_layout()
        fig.savefig(out / f"coherence_sweep_{'history' if mem else 'control'}.png", dpi=150)
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 4.2))
    seed = records[0]['seed']
    for mem in (False, True):
        tt = [r for r in traces if r['seed'] == seed and r['memory_feedback'] == mem]
        ax.plot([r['t'] for r in tt], [r['R_mean'] for r in tt],
                label='H feedback' if mem else 'No H feedback', alpha=.9)
    ax.set(xlabel='Simulation time', ylabel='Mean within-harness coherence R',
           title='Toy model: coherence vs time (one seed)', ylim=(0, 1.05))
    ax.legend(); fig.tight_layout()
    fig.savefig(out / 'coherence_time_comparison.png', dpi=150)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', default='.')
    p.add_argument('--seeds', type=int, nargs='+', default=[7, 11, 19])
    p.add_argument('--plateau', type=float, default=18.0)
    p.add_argument('--dt', type=float, default=0.025)
    p.add_argument('--kmax', type=float, default=5.0)
    p.add_argument('--nk', type=int, default=13)
    args = p.parse_args()
    if args.dt <= 0 or args.plateau <= 0 or args.nk < 3 or args.kmax <= 0:
        p.error('invalid positive simulation parameters')
    out = Path(args.out)
    (out/'results').mkdir(parents=True, exist_ok=True)
    (out/'figures').mkdir(parents=True, exist_ok=True)
    recs, traces = [], []
    for seed in args.seeds:
        for mem in (False, True):
            a,b=simulate(seed,mem,args.plateau,args.dt,args.kmax,args.nk)
            recs.extend(a); traces.extend(b)
    save_csv(out/'results'/'sweep.csv', recs)
    save_csv(out/'results'/'trace.csv', traces)
    make_figures(out/'figures', recs, traces)
    # Area between UP and DOWN curves is finite-rate sweep discrepancy;
    # NOT rigorous hysteresis unless it persists when plateau is prolonged.
    diagnostics = []
    for seed in args.seeds:
        for mem in (False,True):
            up = [r for r in recs if r['seed']==seed and r['memory_feedback']==mem and r['phase']=='up']
            down = [r for r in recs if r['seed']==seed and r['memory_feedback']==mem and r['phase']=='down']
            # Compare only common K values. The down sweep omits the repeated Kmax point.
            kd = np.array([r['K'] for r in down]); rd=np.array([r['R_mean'] for r in down])
            ku = np.array([r['K'] for r in up[:-1]]); ru=np.array([r['R_mean'] for r in up[:-1]])
            diff = ru - np.interp(ku, kd[::-1], rd[::-1])
            area = float(np.sum(0.5*(np.abs(diff[1:])+np.abs(diff[:-1]))*np.diff(ku)))
            diagnostics.append({'seed':seed,'memory_feedback':mem,'finite_rate_sweep_area':area})
    (out/'results'/'diagnostics.json').write_text(json.dumps(diagnostics, indent=2), encoding='utf-8')
    (out/'results'/'manifest.json').write_text(json.dumps({
        'description':'Exploratory inertial oscillator toy model, not LLM or goal drift data',
        'seeds':args.seeds,'plateau':args.plateau,'dt':args.dt,'kmax':args.kmax,
        'nk':args.nk,'n_groups':3,'n_per_group':8,'inertia':1.3,'damping':0.7,
        'omega_std':0.75,'out_ratio':0.16,'alpha_in':0.10,'alpha_out':0.25,
        'tau_h':24.0,'memory_gain':0.85,'integration':'semi-implicit Euler',
        'caveats':['Finite-rate loop != established hysteresis',
                   'R does not measure correctness or goal adherence',
                   'No Lyapunov or chimera-state test performed',
                   'No LLM agents were simulated']},indent=2),encoding='utf-8')
    print('Saved', len(recs),'plateau records; area diagnostics:',diagnostics)

if __name__=='__main__': main()

"""
timetable_ga.py
A framework-independent Genetic Algorithm engine for a school timetable system.

The module has no Django or database dependency. Convert Django model rows into the
dataclasses below, call the engine, then save the returned assignments using Django ORM.

Core design:
- One Gene represents one required lesson/period.
- Each gene has a list of feasible candidate assignments.
- A chromosome chooses exactly one candidate for every gene.
- Locked assignments represent unaffected timetable entries and are never changed.
- Hard conflicts: class, teacher, or room double-booking.
- Soft objective: balanced teacher workload and avoiding repeated same-subject
  periods for a class on the same day.

For temporary substitution, create genes only for affected lessons and pass all
unaffected timetable entries as locked_assignments. The original/general timetable
is therefore not modified by this engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Sequence, Tuple
import random
import statistics


@dataclass(frozen=True)
class Slot:
    slot_id: str
    day: str
    period: int


@dataclass(frozen=True)
class Teacher:
    teacher_id: str
    name: str
    subjects: frozenset[str]
    unavailable_slots: frozenset[str] = frozenset()
    max_periods_per_day: Optional[int] = None


@dataclass(frozen=True)
class Room:
    room_id: str
    name: str
    room_type: str = "regular"
    capacity: int = 9999


@dataclass(frozen=True)
class Assignment:
    lesson_id: str
    class_id: str
    subject_id: str
    teacher_id: str
    room_id: str
    slot_id: str
    day: str
    period: int


@dataclass(frozen=True)
class Candidate:
    teacher_id: str
    room_id: str
    slot_id: str
    day: str
    period: int


@dataclass
class Gene:
    """A required lesson and all feasible ways of scheduling it."""
    lesson_id: str
    class_id: str
    subject_id: str
    candidates: List[Candidate]


@dataclass
class GAConfig:
    population_size: int = 100
    generations: int = 250
    mutation_rate: float = 0.08
    crossover_rate: float = 0.85
    tournament_size: int = 4
    elite_count: int = 3
    random_seed: Optional[int] = 17
    hard_conflict_penalty: int = 100_000
    workload_weight: float = 2.0
    same_subject_same_day_weight: float = 1.5


@dataclass
class GAResult:
    assignments: List[Assignment]
    fitness: float
    hard_conflicts: List[str]
    soft_penalty: float
    generations_run: int
    feasible: bool
    report: Dict[str, object] = field(default_factory=dict)


def make_candidate_assignments(
    lesson_id: str,
    class_id: str,
    subject_id: str,
    slots: Sequence[Slot],
    teachers: Sequence[Teacher],
    rooms: Sequence[Room],
    *,
    required_room_type: str = "regular",
    class_size: int = 0,
    excluded_teacher_ids: Sequence[str] = (),
    allowed_slot_ids: Optional[Sequence[str]] = None,
) -> Gene:
    """
    Build feasible candidates for a lesson.
    Teacher must know the subject and be available; room must meet type/capacity.
    """
    excluded = set(excluded_teacher_ids)
    allowed_slots = set(allowed_slot_ids) if allowed_slot_ids is not None else None
    candidates: List[Candidate] = []
    for slot in slots:
        if allowed_slots is not None and slot.slot_id not in allowed_slots:
            continue
        for teacher in teachers:
            if subject_id not in teacher.subjects:
                continue
            if teacher.teacher_id in excluded:
                continue
            if slot.slot_id in teacher.unavailable_slots:
                continue
            for room in rooms:
                if room.room_type != required_room_type:
                    continue
                if room.capacity < class_size:
                    continue
                candidates.append(Candidate(
                    teacher_id=teacher.teacher_id,
                    room_id=room.room_id,
                    slot_id=slot.slot_id,
                    day=slot.day,
                    period=slot.period,
                ))
    return Gene(lesson_id, class_id, subject_id, candidates)


def _to_assignment(gene: Gene, candidate: Candidate) -> Assignment:
    return Assignment(
        lesson_id=gene.lesson_id,
        class_id=gene.class_id,
        subject_id=gene.subject_id,
        teacher_id=candidate.teacher_id,
        room_id=candidate.room_id,
        slot_id=candidate.slot_id,
        day=candidate.day,
        period=candidate.period,
    )


def _conflicts(assignments: Sequence[Assignment]) -> List[str]:
    """Find class, teacher and room double-bookings in the same time slot."""
    conflicts: List[str] = []
    by_slot = defaultdict(list)
    for a in assignments:
        by_slot[a.slot_id].append(a)

    for slot_id, rows in by_slot.items():
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                a, b = rows[i], rows[j]
                if a.class_id == b.class_id:
                    conflicts.append(
                        f"Class conflict: {a.class_id} has {a.lesson_id} and "
                        f"{b.lesson_id} in slot {slot_id}"
                    )
                if a.teacher_id == b.teacher_id:
                    conflicts.append(
                        f"Teacher conflict: {a.teacher_id} has {a.lesson_id} and "
                        f"{b.lesson_id} in slot {slot_id}"
                    )
                if a.room_id == b.room_id:
                    conflicts.append(
                        f"Room conflict: {a.room_id} is used by {a.lesson_id} and "
                        f"{b.lesson_id} in slot {slot_id}"
                    )
    return conflicts


def _soft_penalty(
    assignments: Sequence[Assignment],
    base_teacher_workload: Optional[Dict[str, int]],
    config: GAConfig,
) -> float:
    # Include existing workload when optimizing temporary substitute assignments.
    workload = Counter(base_teacher_workload or {})
    for a in assignments:
        workload[a.teacher_id] += 1

    values = list(workload.values())
    workload_penalty = statistics.pvariance(values) if len(values) > 1 else 0.0

    # Penalize a class having the same subject more than once on a day.
    subject_day = Counter((a.class_id, a.subject_id, a.day) for a in assignments)
    repeat_penalty = sum(max(0, count - 1) for count in subject_day.values())

    return (
        config.workload_weight * workload_penalty
        + config.same_subject_same_day_weight * repeat_penalty
    )


def _evaluate(
    genes: Sequence[Gene],
    chromosome: Sequence[int],
    locked: Sequence[Assignment],
    base_workload: Optional[Dict[str, int]],
    config: GAConfig,
) -> Tuple[float, List[str], float, List[Assignment]]:
    chosen = [
        _to_assignment(gene, gene.candidates[index])
        for gene, index in zip(genes, chromosome)
    ]
    all_assignments = list(locked) + chosen
    conflicts = _conflicts(all_assignments)
    soft = _soft_penalty(chosen, base_workload, config)
    fitness = len(conflicts) * config.hard_conflict_penalty + soft
    return fitness, conflicts, soft, chosen


def run_genetic_algorithm(
    genes: Sequence[Gene],
    *,
    locked_assignments: Sequence[Assignment] = (),
    base_teacher_workload: Optional[Dict[str, int]] = None,
    config: Optional[GAConfig] = None,
) -> GAResult:
    """
    Optimize a timetable or a temporary substitute plan.

    Every Gene must have at least one feasible candidate. An empty gene means
    the input constraints are impossible and is reported explicitly.
    """
    config = config or GAConfig()
    if not genes:
        return GAResult([], 0.0, [], 0.0, 0, True,
                        {"message": "No lessons were supplied."})

    empty = [g.lesson_id for g in genes if not g.candidates]
    if empty:
        return GAResult([], float("inf"),
                        [f"No feasible teacher/room/slot candidate for {x}" for x in empty],
                        float("inf"), 0, False,
                        {"unassigned_lessons": empty})

    rng = random.Random(config.random_seed)
    population_size = max(2, config.population_size)
    population = [
        [rng.randrange(len(g.candidates)) for g in genes]
        for _ in range(population_size)
    ]

    def score(chromosome):
        return _evaluate(genes, chromosome, locked_assignments,
                         base_teacher_workload, config)

    best_chromosome = None
    best_eval = None
    generations_run = 0

    for generation in range(config.generations + 1):
        ranked = sorted(((score(ch), ch) for ch in population),
                        key=lambda item: item[0][0])
        if best_eval is None or ranked[0][0][0] < best_eval[0]:
            best_eval, best_chromosome = ranked[0][0], ranked[0][1][:]
        generations_run = generation

        if not best_eval[1]:
            break
        if generation == config.generations:
            break

        next_population = [ch[:] for _, ch in ranked[:max(0, config.elite_count)]]

        def tournament():
            contestants = rng.sample(population, min(config.tournament_size, len(population)))
            return min(contestants, key=lambda ch: score(ch)[0])

        while len(next_population) < population_size:
            p1, p2 = tournament()[:], tournament()[:]
            if len(genes) > 1 and rng.random() < config.crossover_rate:
                point = rng.randint(1, len(genes) - 1)
                child1 = p1[:point] + p2[point:]
                child2 = p2[:point] + p1[point:]
            else:
                child1, child2 = p1, p2

            for child in (child1, child2):
                for i, gene in enumerate(genes):
                    if rng.random() < config.mutation_rate and len(gene.candidates) > 1:
                        options = [x for x in range(len(gene.candidates)) if x != child[i]]
                        child[i] = rng.choice(options)
                next_population.append(child)
                if len(next_population) >= population_size:
                    break
        population = next_population

    fitness, conflicts, soft, chosen = _evaluate(
        genes, best_chromosome, locked_assignments, base_teacher_workload, config
    )
    return GAResult(
        assignments=chosen,
        fitness=fitness,
        hard_conflicts=conflicts,
        soft_penalty=soft,
        generations_run=generations_run,
        feasible=(len(conflicts) == 0),
        report={
            "lessons_requested": len(genes),
            "lessons_assigned": len(chosen),
            "locked_assignments": len(locked_assignments),
            "hard_conflict_count": len(conflicts),
            "soft_penalty": soft,
        },
    )


def allocate_substitutes(
    affected_genes: Sequence[Gene],
    *,
    unaffected_timetable: Sequence[Assignment],
    current_teacher_workload: Dict[str, int],
    config: Optional[GAConfig] = None,
) -> GAResult:
    """
    Allocate substitutes for affected lessons only.

    Build each affected Gene's candidates using make_candidate_assignments().
    Exclude the absent teacher from those candidates. Pass all unaffected
    timetable lessons as locked assignments so their teachers/classes/rooms
    cannot be double-booked. This returns a temporary plan; it does not mutate
    or overwrite the general timetable.
    """
    return run_genetic_algorithm(
        affected_genes,
        locked_assignments=unaffected_timetable,
        base_teacher_workload=current_teacher_workload,
        config=config,
    )


def validate_required_periods(
    assignments: Sequence[Assignment],
    required_periods: Dict[Tuple[str, str], int],
) -> Dict[str, object]:
    """
    Compare assigned lesson counts with {(class_id, subject_id): required_count}.
    Normally create one Gene per required period; this independent check catches
    missing or excess lesson records before saving.
    """
    actual = Counter((a.class_id, a.subject_id) for a in assignments)
    rows = []
    valid = True
    for key, required in required_periods.items():
        found = actual[key]
        ok = found == required
        valid = valid and ok
        rows.append({
            "class_id": key[0],
            "subject_id": key[1],
            "required": required,
            "assigned": found,
            "status": "OK" if ok else "MISMATCH",
        })
    return {"valid": valid, "details": rows}

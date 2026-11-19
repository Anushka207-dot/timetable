import random

def generate_timetable(config, population_size=100, generations=250):
    # Each required weekly lesson becomes a gene; its value is a day-period slot.
    days=config['days']; period_count=int(config['periods'])
    slots=[(d,p) for d in range(len(days)) for p in range(period_count)]
    classes=config['classes']
    lessons=[]
    for class_index, classroom in enumerate(classes):
        for subject in classroom['subjects']:
            for _ in range(int(subject['weekly_periods'])):
                lessons.append({'class_index':class_index,'subject':subject['name'],'teacher':subject['teacher']})
    if not lessons: raise ValueError('Add at least one subject and weekly period count.')
    if len(lessons) > len(classes)*len(slots):
        raise ValueError('There are more weekly lessons than available class-period slots.')

    def fitness(chromosome):
        penalty=0
        class_slots=set()
        teacher_slots=set()
        subject_day=set()
        for gene, slot_index in zip(lessons, chromosome):
            day, period=slots[slot_index]
            class_key=(gene['class_index'],slot_index)
            teacher_key=(gene['teacher'].strip().lower(),slot_index)
            subject_key=(gene['class_index'],gene['subject'],day)
            if class_key in class_slots: penalty += 1000
            if teacher_key in teacher_slots: penalty += 1000
            if subject_key in subject_day: penalty += 10
            class_slots.add(class_key); teacher_slots.add(teacher_key); subject_day.add(subject_key)
        return penalty

    def create_individual():
        # Distinct slots per class ensure no class receives two lessons in one period.
        genes=[None]*len(lessons)
        by_class={}
        for i,lesson in enumerate(lessons): by_class.setdefault(lesson['class_index'],[]).append(i)
        for indices in by_class.values():
            chosen=random.sample(range(len(slots)),len(indices))
            for i,s in zip(indices,chosen): genes[i]=s
        return genes

    population=[create_individual() for _ in range(population_size)]
    for _ in range(generations):
        population.sort(key=fitness)
        if fitness(population[0])==0: break
        parents=population[:max(8,population_size//5)]
        next_population=parents[:]
        while len(next_population)<population_size:
            a,b=random.sample(parents,2)
            cut=random.randrange(len(lessons))
            child=a[:cut]+b[cut:]
            if random.random()<0.25:
                i=random.randrange(len(child)); child[i]=random.randrange(len(slots))
            # Repair same-class slot collisions
            seen={}
            for i,lesson in enumerate(lessons):
                ci=lesson['class_index']; seen.setdefault(ci,set())
                if child[i] in seen[ci]:
                    available=[s for s in range(len(slots)) if s not in seen[ci]]
                    if available: child[i]=random.choice(available)
                seen[ci].add(child[i])
            next_population.append(child)
        population=next_population
    best=min(population,key=fitness)
    result=[]
    for ci, classroom in enumerate(classes):
        day_rows=[]
        for d,day in enumerate(days):
            cells=[]
            for p in range(period_count):
                match=next((lesson for i,lesson in enumerate(lessons)
                            if lesson['class_index']==ci and best[i]==d*period_count+p),None)
                cells.append({'subject':match['subject'],'teacher':match['teacher']} if match else None)
            day_rows.append({'day':day,'periods':cells})
        result.append({'class_name':classroom['name'],'section':classroom['section'],'days':day_rows})
    return result

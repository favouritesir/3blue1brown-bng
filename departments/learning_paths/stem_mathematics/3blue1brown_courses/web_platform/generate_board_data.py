import os, glob, json

web = r'departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform'
parent = r'departments/learning_paths/stem_mathematics/3blue1brown_courses'

courses_def = [
    {
        'id': 'linear_algebra',
        'title': 'Essence of Linear Algebra',
        'title_bn': 'লিনিয়ার অ্যালজেব্রা',
        'badge': 'Core Foundation',
        'accent': '#74C0E3',
        'total': 15,
        'parent_dir': 'essence_of_linear_algebra',
        'data_dir': 'linear_algebra',
        'web_dir': 'courses/linear_algebra',
        'audio_dir': 'linear_algebra',
        'lesson_titles': {
            '01': ('Vectors, what even are they?', 'ভেক্টর আসলে কী?'),
            '02': ('Linear combinations, span, and basis vectors', 'রৈখিক সমন্বয়, স্প্যান ও ভিত্তি ভেক্টর'),
            '03': ('Linear transformations and matrices', 'রৈখিক রূপান্তর ও ম্যাট্রিক্স'),
            '04': ('Matrix multiplication as composition', 'ম্যাট্রিক্স গুণন — রূপান্তরের রচনা'),
            '05': ('Three-dimensional linear transformations', 'ত্রিমাত্রিক রৈখিক রূপান্তর'),
            '06': ('The determinant', 'নির্ণায়ক বা ডিটারমিন্যান্ট'),
            '07': ('Inverse matrices, column space and null space', 'বিপরীত ম্যাট্রিক্স, কলাম স্পেস ও শূন্য স্পেস'),
            '08': ('Nonsquare matrices as transformations between dimensions', 'অসম আকারের ম্যাট্রিক্স ও মাত্রার রূপান্তর'),
            '09': ('Dot products and duality', 'ডট প্রোডাক্ট ও ডুয়ালিটি (দ্বৈততা)'),
            '10': ('Cross products', 'ক্রস গুণন ও জ্যামিতিক ওরিয়েন্টেশন'),
            '11': ('Cross products in the light of linear transformations', 'রৈখিক রূপান্তরের আলোকে ক্রস প্রোডাক্ট ও ডুয়ালিটি'),
            '12': ('Cramer\'s rule, explained geometrically', 'ক্র্যামারের নিয়ম: একটি জ্যামিতিক ব্যাখ্যা'),
            '13': ('Change of basis', 'ভিত্তি পরিবর্তন ও ভিন্ন দৃষ্টিভঙ্গির রূপান্তর'),
            '14': ('Eigenvectors and eigenvalues', 'আইগেনভেক্টর ও আইগেনভ্যালু'),
            '15': ('Abstract vector spaces', 'বিমূর্ত ভেক্টর স্পেস ও ফাংশন স্পেস')
        }
    },
    {
        'id': 'calculus',
        'title': 'Essence of Calculus',
        'title_bn': 'ক্যালকুলাস',
        'badge': 'Continuity & Change',
        'accent': '#38bdf8',
        'total': 12,
        'parent_dir': 'essence_of_calculus',
        'data_dir': 'calculus',
        'web_dir': 'courses/calculus',
        'audio_dir': 'calculus',
        'lesson_titles': {
            '01': ('The Essence of Calculus', 'ক্যালকুলাসের মূল সারমর্ম — ক্ষেত্রফল ও ঢালের রহস্য'),
            '02': ('The Paradox of the Derivative', 'অন্তরজের হেঁয়ালি — তাৎক্ষণিক বেগ ও পরিবর্তনের হার'),
            '03': ('Derivative Formulas Through Geometry', 'জ্যামিতির মাধ্যমে অন্তরজের সূত্র'),
            '04': ('Visualizing the Chain Rule and Product Rule', 'চেইন রুল ও প্রোডাক্ট রুলের জ্যামিতিক রূপ'),
            '05': ('What\'s so special about Euler\'s number e?', 'অয়লার সংখ্যা e কেন এত বিশেষ?'),
            '06': ('Implicit Differentiation', 'অপ্রত্যক্ষ অন্তরীকরণ বা প্রচ্ছন্ন ব্যবকলন'),
            '07': ('Limits, L\'Hopital\'s rule, and epsilon-delta', 'সীমা বা লিমিট, লা হসপিটাল রুল ও এপসিলন-ডেল্টা'),
            '08': ('Integration & The Fundamental Theorem', 'যোগজীকরণ ও ক্যালকুলাসের মৌলিক উপপাদ্য'),
            '09': ('What does area have to do with slope?', 'ক্ষেত্রফলের সাথে ঢালের কী সম্পর্ক?'),
            '10': ('Higher order derivatives', 'উচ্চতর মাত্রার অন্তরজ বা হায়ার অর্ডার ডেরিভেটিভ'),
            '11': ('Taylor series', 'টেইলর ধারা ও পলিনোমিয়াল আসন্নায়ন'),
            '12': ('What is a derivative really?', 'অন্তরজ আসলে কী? — চূড়ান্ত সারমর্ম')
        }
    },
    {
        'id': 'neural_networks',
        'title': 'Neural Networks',
        'title_bn': 'নিউরাল নেটওয়ার্ক',
        'badge': 'Deep Learning AI',
        'accent': '#c084fc',
        'total': 4,
        'parent_dir': 'neural_networks',
        'data_dir': 'neural_networks',
        'web_dir': 'courses/neural_networks',
        'audio_dir': 'neural_networks',
        'lesson_titles': {
            '01': ('But what is a neural network?', 'নিউরাল নেটওয়ার্ক আসলে কী?'),
            '02': ('Gradient descent, how neural networks learn', 'গ্র্যাডিয়েন্ট ডিসেন্ট: নেটওয়ার্ক কীভাবে শেখে?'),
            '03': ('What is backpropagation really doing?', 'ব্যাকপ্রপাগেশন আসলে কী করে?'),
            '04': ('Backpropagation calculus', 'ব্যাকপ্রপাগেশন ক্যালকুলাস: বিস্তারিত প্রমাণ ও অ্যালগরিদম')
        }
    },
    {
        'id': 'differential_equations',
        'title': 'Differential Equations',
        'title_bn': 'ডিফারেনশিয়াল সমীকরণ',
        'badge': 'Dynamical Systems',
        'accent': '#48bb78',
        'total': 6,
        'parent_dir': 'differential_equations',
        'data_dir': 'differential_equations',
        'web_dir': 'courses/differential_equations',
        'audio_dir': 'differential_equations',
        'lesson_titles': {
            '01': ('Differential equations, studying the unsolvable', 'ডিফারেনশিয়াল সমীকরণ কী? — পরিবর্তনের ভাষা'),
            '02': ('The Pendulum and Phase Space', 'পেন্ডুলাম মেকানিক্স এবং ফেজ স্পেস'),
            '03': ('The Heat Equation and Fourier Series', 'তাপ সমীকরণ এবং ফুরিয়ার ধারা'),
            '04': ('Exponential decay, growth and Euler\'s number', 'এক্সপোনেনশিয়াল ক্ষয়, বৃদ্ধি ও অয়লার সংখ্যা'),
            '05': ('Phase portraits and linear systems of ODEs', 'ফেজ পোর্ট্রেট এবং লিনিয়ার ওডিই সিস্টেম'),
            '06': ('Lorenz attractor, chaos and bifurcations', 'লরেঞ্জ অ্যাট্রাক্টর, ক্যাওস এবং বাইফারকেশন')
        }
    },
    {
        'id': 'probability',
        'title': 'Essence of Probability',
        'title_bn': 'সম্ভাব্যতা তত্ত্ব',
        'badge': 'Uncertainty & Bayes',
        'accent': '#f6ad55',
        'total': 6,
        'parent_dir': 'essence_of_probability',
        'data_dir': 'probability',
        'web_dir': 'courses/probability',
        'audio_dir': 'probability',
        'lesson_titles': {
            '01': ('What even is probability? — The geometry of uncertainty', 'সম্ভাব্যতা আসলে কী? — অনিশ্চয়তার জ্যামিতি'),
            '02': ('Bayes\' Rule & The Medical Paradox', 'বেজের সূত্র এবং মেডিকেল টেস্ট প্যারাডক্স'),
            '03': ('Binomial distributions and coin flips', 'দ্বিপদী বিন্যাস ও কয়েন টসের জ্যামিতি'),
            '04': ('Poisson processes and waiting times', 'পয়সোঁ প্রক্রিয়া ও অপেক্ষার সময়'),
            '05': ('Markov Chains, Random Walks, and Steady States', 'মার্কভ চেইন, র‍্যান্ডম ওয়াক ও স্টেডি স্টেট'),
            '06': ('Continuous probability distributions & Central Limit Theorem', 'অবিচ্ছিন্ন সম্ভাবনা বিন্যাস ও সেন্ট্রাল লিমিট থিওরেম')
        }
    },
    {
        'id': 'lockdown_math',
        'title': 'Lockdown Math',
        'title_bn': 'লকডাউন ম্যাথ',
        'badge': 'Live Interactive Gems',
        'accent': '#f43f5e',
        'total': 10,
        'parent_dir': 'lockdown_math',
        'data_dir': 'lockdown_math',
        'web_dir': 'courses/lockdown_math',
        'audio_dir': 'lockdown_math',
        'lesson_titles': {
            '01': ('The quadratic formula visually', 'দ্বিঘাত সমীকরণের আসল জ্যামিতিক রূপ'),
            '02': ('Exponential growth and epidemics', 'এক্সপোনেনশিয়াল বৃদ্ধি ও মহামারির গণিত'),
            '03': ('Trigonometric formulas and geometry', 'ত্রিকোণমিতিক সূত্র ও জ্যামিতি'),
            '04': ('Area and Pi with circle unwrapping', 'বৃত্তের ক্ষেত্রফল ও পাই-এর উন্মোচন'),
            '05': ('Binomial distributions & Pascal\'s triangle', 'দ্বিপদী বণ্টন ও প্যাসকেলের ত্রিভুজ'),
            '06': ('Prime numbers and modular arithmetic', 'মৌলিক সংখ্যা ও মডুলার অ্যারিথমেটিক'),
            '07': ('Complex numbers visually', 'জটিল সংখ্যার জ্যামিতিক রূপ'),
            '08': ('Vectors & linear transformations revisited', 'ভেক্টর ও রৈখিক রূপান্তর পর্যালোচনা'),
            '09': ('Calculus without limits', 'সীমা ছাড়া ক্যালকুলাস'),
            '10': ('The beauty of pure mathematics', 'বিশুদ্ধ গণিতের অপার সৌন্দর্য')
        }
    }
]

catalog_data = []

for c in courses_def:
    cid = c['id']
    course_obj = {
        'id': cid,
        'title': c['title'],
        'title_bn': c['title_bn'],
        'badge': c['badge'],
        'accent': c['accent'],
        'total': c['total'],
        'lessons': []
    }
    
    for num in range(1, c['total'] + 1):
        num_str = f'{num:02d}'
        
        # HTML Page
        html_rel = f"courses/{cid}/lesson_{num_str}.html"
        html_abs = os.path.join(web, html_rel)
        has_html = os.path.isfile(html_abs)
        
        # Data JSON
        data_rel = f"data/{c['data_dir']}/lesson_{num_str}.json"
        data_abs = os.path.join(web, data_rel)
        has_data = os.path.isfile(data_abs)
        
        # Audio Manifest
        manifest_rel = f"assets/audio/{c['audio_dir']}/lesson_{num_str}/manifest.js"
        manifest_abs = os.path.join(web, manifest_rel)
        has_manifest = os.path.isfile(manifest_abs)
        
        # Audio segments
        audio_folder = os.path.join(web, f"assets/audio/{c['audio_dir']}/lesson_{num_str}")
        audio_count = len(glob.glob(os.path.join(audio_folder, '*.mp3'))) if os.path.isdir(audio_folder) else 0
        
        # Media vault master audio & video.
        # A lesson counts as having a dubbed video if EITHER the canonical
        # file exists OR the component-first pipeline produced an experiment
        # full-dubbed master (video stream copy + clean Bengali narration).
        has_vault_mp3 = False
        has_vault_mp4 = False
        vault_mp3_rel = None
        vault_mp4_rel = None
        if cid == 'linear_algebra':
            vault_mp3_rel = f"media_vault/lesson_{num_str}/3b1b_lesson_{num_str}_bangla_master.mp3"
            canonical_video = f"media_vault/lesson_{num_str}/3b1b_lesson_{num_str}_bangla_dubbed_video.mp4"
            experiment_videos = glob.glob(os.path.join(web, 'media_vault', f'lesson_{num_str}', 'experiments', '*full_dubbed*.mp4'))
            if experiment_videos:
                vault_mp4_rel = os.path.relpath(experiment_videos[0], web).replace('\\', '/')
                has_vault_mp4 = True
            elif os.path.isfile(os.path.join(web, canonical_video)):
                vault_mp4_rel = canonical_video
                has_vault_mp4 = True
            has_vault_mp3 = os.path.isfile(os.path.join(web, vault_mp3_rel))
        
        # Master script in project dubbing pipelines
        ms_files = []
        for pat in [f"*lesson_{num_str}*/**/*master_script*.json", f"*l{num_str}*/**/*master_script*.json", f"*lesson_{num_str}_*master_script*.json"]:
            ms_files.extend(glob.glob(os.path.join(parent, c['parent_dir'], pat), recursive=True))
        if not ms_files and cid == 'calculus':
            ms_files.extend(glob.glob(os.path.join(parent, 'calculus', f"*lesson_{num_str}*/**/*master_script*.json"), recursive=True))
        has_ms = len(ms_files) > 0 or has_data
        
        # Features
        uses_components = False
        has_katex = False
        has_quiz = False
        has_lab = False
        has_narration = False
        
        if has_html:
            with open(html_abs, 'r', encoding='utf-8', errors='ignore') as f:
                raw = f.read()
                uses_components = '<b1b-' in raw
                has_katex = 'katex' in raw.lower()
                has_quiz = 'quiz' in raw.lower() or '<b1b-quiz' in raw
                has_lab = 'canvas' in raw.lower() or 'visualizer' in raw.lower() or 'interactive' in raw.lower()
                has_narration = 'narration' in raw.lower() or 'manifest.js' in raw.lower()
                
        if has_data:
            try:
                with open(data_abs, 'r', encoding='utf-8', errors='ignore') as f:
                    dj = json.load(f)
                    if 'quizzes' in dj and len(dj['quizzes']) > 0:
                        has_quiz = True
                    if 'formulas' in str(dj) or 'katex' in str(dj).lower():
                        has_katex = True
                    if 'interactive_components' in dj or 'visualizer' in str(dj).lower():
                        has_lab = True
            except:
                pass
                
        # Titles
        titles = c['lesson_titles'].get(num_str, (f'Lesson {num_str}', f'অধ্যায় {num_str}'))
        
        # Status calculation:
        # 'completed' ONLY IF: has_html AND has_vault_mp4 AND has_vault_mp3 AND has_katex AND fully_audited
        # Currently, Lessons are marked 'in_production' or 'live' while undergoing 100% 3B1B parity audit
        # Canonical tracking (post-audit):
        #   completed    = fully verified, component-based, parity-checked (Lesson 01 only for now)
        #   under_review = assets exist but must be re-audited to Lesson 01 standard
        #   planned      = nothing produced yet
        completed_ids_path = os.path.join(web, 'governance', 'completed_lessons.json')
        with open(completed_ids_path, 'r', encoding='utf-8') as f:
            completed_ids = set(json.load(f).get('completed_lessons', []))
        lesson_id = f"{cid}_l{num_str}"
        if lesson_id in completed_ids:
            status = 'completed'
        elif has_html or has_data or has_manifest or has_ms or audio_count > 0:
            status = 'under_review'
        else:
            status = 'planned'
            
        course_obj['lessons'].append({
            'id': f"{cid}_l{num_str}",
            'num': num_str,
            'title_en': titles[0],
            'title_bn': titles[1],
            'status': status,
            'has_html': has_html,
            'html_path': html_rel if has_html else None,
            'has_data': has_data,
            'data_path': data_rel if has_data else None,
            'has_manifest': has_manifest,
            'manifest_path': manifest_rel if has_manifest else None,
            'audio_count': audio_count,
            'has_vault_mp3': has_vault_mp3,
            'has_vault_mp4': has_vault_mp4,
            'has_master_script': has_ms,
            'uses_components': uses_components,
            'has_katex': has_katex,
            'has_quiz': has_quiz,
            'has_lab': has_lab,
            'has_narration': has_narration
        })
        
    catalog_data.append(course_obj)

with open(os.path.join(web, 'board_data.json'), 'w', encoding='utf-8') as f:
    json.dump(catalog_data, f, ensure_ascii=False, indent=2)
print('Successfully generated board_data.json')

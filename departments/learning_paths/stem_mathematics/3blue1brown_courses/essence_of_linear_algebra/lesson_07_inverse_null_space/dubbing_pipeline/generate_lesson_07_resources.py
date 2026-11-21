import json
import os
from pathlib import Path

BASE_DIR = Path(r"D:\0PEN CODE\Dub Studio")

# 1. Target Paths
MASTER_SCRIPT_DIR = BASE_DIR / "departments" / "learning_paths" / "stem_mathematics" / "3blue1brown_courses" / "essence_of_linear_algebra" / "lesson_07_inverse_null_space" / "dubbing_pipeline"
MASTER_SCRIPT_FILE = MASTER_SCRIPT_DIR / "3b1b_lesson_07_bangla_master_script.json"

AUDIO_DIR = BASE_DIR / "departments" / "learning_paths" / "stem_mathematics" / "3blue1brown_courses" / "web_platform" / "assets" / "audio" / "linear_algebra" / "lesson_07"
AUDIO_MANIFEST_JSON = AUDIO_DIR / "manifest.json"
AUDIO_MANIFEST_JS = AUDIO_DIR / "manifest.js"

DATA_DIR = BASE_DIR / "departments" / "learning_paths" / "stem_mathematics" / "3blue1brown_courses" / "web_platform" / "data" / "linear_algebra"
LESSON_DATA_FILE = DATA_DIR / "lesson_07.json"

MASTER_SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Define Section Cues and Script Data
SECTIONS_DATA = [
    {
        "section_id": "sec_01_linear_systems",
        "title": "জ্যামিতিক দৃষ্টিকোণ থেকে লিনিয়ার সমীকরণ জোট",
        "title_en": "Linear Systems from a Geometric Perspective",
        "audio_file": "sec_01_linear_systems.mp3",
        "cues_file": "sec_01_linear_systems_cues.json",
        "summary_bn": "লিনিয়ার সমীকরণ জোটকে শুধুমাত্র প্রতীকের হিসাব হিসেবে না দেখে স্থান রূপান্তরের জ্যামিতিক প্রক্রিয়া হিসেবে অনুধাবন করা।",
        "key_takeaways": [
            "লিনিয়ার সমীকরণ জোটকে সংক্ষেপে ম্যাট্রিক্স-ভেক্টর সমীকরণ $A\\vec{x} = \\vec{v}$ আকারে প্রকাশ করা যায়।",
            "ম্যাট্রিক্স $A$ একটি রৈখিক রূপান্তর নির্দেশ করে, যা অজানা ভেক্টর $\\vec{x}$-কে পরিচিত ভেক্টর $\\vec{v}$-তে রূপান্তরিত করে।",
            "সমীকরণ সমাধানের জ্যামিতিক অর্থ হলো: কোন ইনপুট ভেক্টর $\\vec{x}$ রূপান্তরের পর নির্দিষ্ট ভেক্টর $\\vec{v}$-এর অবস্থানে গিয়ে পৌঁছায় তা খুঁজে বের করা।"
        ],
        "formulas": [
            {
                "label": "বীজগাণিতিক সমীকরণ জোট",
                "katex": "\\begin{cases} 2x + 2y = -4 \\\\ x + 3y = -1 \\end{cases}"
            },
            {
                "label": "ম্যাট্রিক্স-ভেক্টর রূপান্তর সমীকরণ",
                "katex": "A\\vec{x} = \\vec{v} \\iff \\begin{bmatrix} 2 & 2 \\\\ 1 & 3 \\end{bmatrix} \\begin{bmatrix} x \\\\ y \\end{bmatrix} = \\begin{bmatrix} -4 \\\\ -1 \\end{bmatrix}"
            }
        ],
        "figures": [
            {
                "id": "fig_linear_system_setup",
                "caption_bn": "সমীকরণ জোটকে একটি একক ম্যাট্রিক্স রূপান্তর $A\\vec{x} = \\vec{v}$ রূপে প্রকাশ",
                "type": "svg",
                "src": "figures/linear_system_setup.svg"
            },
            {
                "id": "fig_preimage_search",
                "caption_bn": "কোন আদি ভেক্টর $\\vec{x}$ রূপান্তরের পর $\\vec{v}$-এ পতিত হয় তার অনুসন্ধান",
                "type": "svg",
                "src": "figures/preimage_search.svg"
            }
        ],
        "interactive_widget": {
            "type": "linear_system_solver_visualizer",
            "initial_matrix": [[2, 2], [1, 3]],
            "target_vector": [-4, -1],
            "description_bn": "টার্গেট ভেক্টর $\\vec{v}$ নির্বাচন করে রূপান্তরের পূর্বাবস্থায় ইনপুট ভেক্টর $\\vec{x}$ এর অবস্থান প্রত্যক্ষ করুন।"
        },
        "math_concepts": [
            "Linear system of equations: Ax = v",
            "Matrix-vector multiplication as linear combination",
            "Geometric transformation perspective: finding the pre-image x",
            "Mapping unknown inputs to known outputs"
        ],
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "text": "প্রথম পরিচ্ছেদ: জ্যামিতিক দৃষ্টিকোণ থেকে লিনিয়ার সমীকরণ জোট।",
                "en": "Chapter 1: Linear Systems from a Geometric Perspective.",
                "formula": None,
                "duration_ms": 4200.0
            },
            {
                "index": 1,
                "type": "chapter-quote",
                "text": "গণিতবিদদের মতে: সমীকরণ সমাধান কেবল প্রতীকের শুকনো কাটাকাটি নয়; এটি হলো স্থানকে তার আদি অবস্থানে দেখার এক দূরদর্শী শিল্প।",
                "en": "Solving systems of equations is not mere algebraic symbol manipulation; it is the art of seeing space before it was transformed.",
                "formula": "A\\vec{x} = \\vec{v}",
                "duration_ms": 11500.0
            },
            {
                "index": 2,
                "type": "p",
                "text": "শিক্ষার্থী বন্ধুরা, লিনিয়ার অ্যালজেব্রা কেন বিজ্ঞান ও প্রযুক্তির প্রতিটি শাখায় এত ব্যাপক ব্যবহৃত হয়? তার অন্যতম প্রধান কারণ হলো লিনিয়ার সমীকরণ জোট সমাধানের অভূতপূর্ব সক্ষমতা।",
                "en": "Why is linear algebra so ubiquitously applied across science and engineering? One of the foremost reasons is its unmatched power in solving systems of linear equations.",
                "formula": None,
                "duration_ms": 14200.0
            },
            {
                "index": 3,
                "type": "p",
                "text": "স্কুল-কলেজে আমরা একগাদা অজানা চলক নিয়ে একাধিক সমীকরণ সমাধানের নিয়ম শিখেছি। যেমন: টু এক্স যোগ টু ওয়াই সমান মাইনাস ফোর, এবং এক্স যোগ থ্রি ওয়াই সমান মাইনাস ওয়ান।",
                "en": "In traditional algebra, we learn procedures to solve multiple equations with unknown variables, such as 2x + 2y = -4 and x + 3y = -1.",
                "formula": "\\begin{cases} 2x + 2y = -4 \\\\ x + 3y = -1 \\end{cases}",
                "duration_ms": 13800.0
            },
            {
                "index": 4,
                "type": "formula-box",
                "text": "ম্যাট্রিক্সের চমৎকার নিয়মে এই সমীকরণগুলোকে একটি একক ভেক্টর সম্পর্কে সাজানো যায়: ম্যাট্রিক্স এ গুণ ভেক্টর এক্স সমান ভেক্টর ভি। এখানে এ হলো সহগ ম্যাট্রিক্স, এক্স হলো অজানা ভেক্টর, এবং ভি হলো পরিচিত ফলাফল ভেক্টর।",
                "en": "Using matrix multiplication, these equations consolidate into a single elegant expression: A times vector x equals vector v, where A is the coefficient matrix, x is the unknown vector, and v is the target vector.",
                "formula": "\\begin{bmatrix} 2 & 2 \\\\ 1 & 3 \\end{bmatrix} \\begin{bmatrix} x \\\\ y \\end{bmatrix} = \\begin{bmatrix} -4 \\\\ -1 \\end{bmatrix}",
                "duration_ms": 18500.0
            },
            {
                "index": 5,
                "type": "figure",
                "text": "পাশের চিত্রে লক্ষ্য করুন: আমরা যখন এ গুণ ভেক্টর এক্স সমান ভি লিখি, জ্যামিতিকভাবে এর অর্থ হলো ম্যাট্রিক্স এ স্থানকে একটি সুনির্দিষ্ট উপায়ে রূপান্তরিত করছে।",
                "en": "Looking at the visual diagram, writing A times vector x equals v geometrically means that matrix A acts as a linear transformation warping the space.",
                "formula": None,
                "duration_ms": 11200.0
            },
            {
                "index": 6,
                "type": "insight-box",
                "text": "সুতরাং সমীকরণটি সমাধান করার আসল জ্যামিতিক প্রশ্নটি হলো: রূপান্তরের পূর্বে কোন ভেক্টর এক্সটি ঠিক এমন স্থানে ছিল, যা এ রূপান্তরের পর হুবহু ভেক্টর ভি-এর ওপর গিয়ে পড়েছে?",
                "en": "Therefore, the true geometric problem is: which vector x, before the transformation was applied, landed directly on vector v after the transformation?",
                "formula": "\\text{Question: Which } \\vec{x} \\text{ lands on } \\vec{v}?",
                "duration_ms": 14600.0
            },
            {
                "index": 7,
                "type": "p",
                "text": "এই প্রশ্নটির উত্তর নির্ভর করে রূপান্তর এ স্থানটিকে কীভাবে পরিচালিত করেছে—স্থানটি কি পূর্ণ মাত্রায় বিস্তৃত আছে, নাকি চ্যাপ্টা হয়ে তার মাত্রা হারিয়ে ফেলেছে?",
                "en": "The answer to this question depends fundamentally on what transformation A does to space—does it preserve full dimensions, or squish space into a lower dimension?",
                "formula": None,
                "duration_ms": 10800.0
            }
        ]
    },
    {
        "section_id": "sec_02_inverse_matrices",
        "title": "বিপরীত ম্যাট্রিক্স: রূপান্তরকে পূর্বাবস্থায় ফিরিয়ে আনা",
        "title_en": "The Inverse Matrix: Undoing the Transformation",
        "audio_file": "sec_02_inverse_matrices.mp3",
        "cues_file": "sec_02_inverse_matrices_cues.json",
        "summary_bn": "ডিটারমিন্যান্ট অশূন্য হলে রূপান্তরের বিপরীত প্রক্রিয়া হিসেবে বিপরীত ম্যাট্রিক্স $A^{-1}$ প্রয়োগ করে সরাসরি সমাধান নির্ণয় করা।",
        "key_takeaways": [
            "ডিটারমিন্যান্ট শূন্য না হলে ($\\det(A) \\neq 0$) স্থান সংকুচিত হয় না, ফলে রূপান্তরটিকে পূর্বাবস্থায় ফিরিয়ে আনা সম্ভব।",
            "বিপরীত ম্যাট্রিক্স $A^{-1}$ হলো এমন একটি রূপান্তর যা $A$-এর প্রভাবকে পুরোপুরি বাতিল করে: $A^{-1}A = I$ (আইডেন্টিটি ম্যাট্রিক্স)।",
            "লিনিয়ার সিস্টেম সমাধানের ক্ষেত্রে সমীকরণের উভয় পাশে $A^{-1}$ গুণ করলে অনন্য সমাধান পাওয়া যায়: $\\vec{x} = A^{-1}\\vec{v}$।",
            "ডিটারমিন্যান্ট শূন্য হলে ($\\det(A) = 0$) স্থান চ্যাপ্টা হয়ে যায়; সংকুচিত রেখা বা বিন্দুকে আবার সমতলে ফিরিয়ে আনার কোনো একক বৈধ ফাংশন সম্ভব নয়, তাই $A^{-1}$ বিদ্যমান থাকে না।"
        ],
        "formulas": [
            {
                "label": "অভেদক বা আইডেন্টিটি রূপান্তর",
                "katex": "A^{-1} A = I = \\begin{bmatrix} 1 & 0 \\\\ 0 & 1 \\end{bmatrix}"
            },
            {
                "label": "বিপরীত ম্যাট্রিক্স দ্বারা সমাধান",
                "katex": "A\\vec{x} = \\vec{v} \\implies A^{-1}(A\\vec{x}) = A^{-1}\\vec{v} \\implies \\vec{x} = A^{-1}\\vec{v}"
            },
            {
                "label": "ইনভার্স অস্তিত্বহীনতার শর্ত",
                "katex": "\\det(A) = 0 \\iff A^{-1} \\text{ does not exist}"
            }
        ],
        "figures": [
            {
                "id": "fig_inverse_transformation_undo",
                "caption_bn": "বিপরীত রূপান্তর $A^{-1}$ স্থানকে আবার পূর্বের আকৃতিতে ফিরিয়ে আনে",
                "type": "svg",
                "src": "figures/inverse_transformation_undo.svg"
            },
            {
                "id": "fig_squish_irreversible",
                "caption_bn": "স্থান একবার সংকুচিত হয়ে রেখায় পরিণত হলে তাকে আর এককভাবে সমতলে রূপান্তর করা যায় না",
                "type": "svg",
                "src": "figures/squish_irreversible.svg"
            }
        ],
        "math_concepts": [
            "Non-zero determinant: det(A) != 0",
            "Inverse transformation A^(-1)",
            "Identity matrix I: doing nothing",
            "A^(-1) * A = I",
            "Solving x = A^(-1) * v",
            "Zero determinant: det(A) = 0 and non-invertibility"
        ],
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "text": "দ্বিতীয় পরিচ্ছেদ: বিপরীত ম্যাট্রিক্স ও রূপান্তরের পূর্বাবস্থা।",
                "en": "Chapter 2: The Inverse Matrix and Undoing Transformations.",
                "formula": None,
                "duration_ms": 4500.0
            },
            {
                "index": 1,
                "type": "p",
                "text": "ধরা যাক ম্যাট্রিক্স এ-এর ডিটারমিন্যান্ট শূন্য নয়। অর্থাৎ রূপান্তরটি স্থানকে চ্যাপ্টা করে এক মাত্রা বা শূন্য মাত্রায় সংকুচিত করেনি; সমতল সমতলেই রয়ে গেছে।",
                "en": "Suppose the determinant of matrix A is non-zero. This means the transformation did not squish space into a lower dimension; the plane remains a plane.",
                "formula": "\\det(A) \\neq 0",
                "duration_ms": 12800.0
            },
            {
                "index": 2,
                "type": "p",
                "text": "যেহেতু স্থান সংকুচিত হয়নি, তাই আমরা পুরো রূপান্তরটিকে একদম হুবহু উল্টো দিকে চালিয়ে সমতলকে তার পূর্বের অবস্থায় ফিরিয়ে আনতে পারি! এই উল্টো রূপান্তরটিকেই বলা হয় এ-এর বিপরীত রূপান্তর বা এ ইনভার্স।",
                "en": "Because space wasn't compressed, we can play the transformation backwards to return space to its original state. This reverse transformation is called the inverse of A, denoted A inverse.",
                "formula": "A^{-1}",
                "duration_ms": 16400.0
            },
            {
                "index": 3,
                "type": "figure",
                "text": "স্ক্রিনে লক্ষ্য করুন: ম্যাট্রিক্স এ যদি সমতলকে নব্বই ডিগ্রি ঘড়ির কাঁটার বিপরীতে ঘোরায়, তবে এ ইনভার্স ঠিক নব্বই ডিগ্রি ঘড়ির কাঁটার দিকে ফিরিয়ে নিয়ে আসবে।",
                "en": "On screen, observe that if matrix A rotates the plane 90 degrees counterclockwise, A inverse rotates it 90 degrees clockwise back to start.",
                "formula": None,
                "duration_ms": 12200.0
            },
            {
                "index": 4,
                "type": "formula-box",
                "text": "যদি আপনি প্রথমে এ রূপান্তর প্রয়োগ করেন এবং ঠিক তারপর এ ইনভার্স রূপান্তর প্রয়োগ করেন, তবে স্থানের কোনো ভেক্টরই বিন্দুমাত্র নড়বে না। গণিতে একে বলা হয় আইডেন্টিটি বা অভেদক রূপান্তর।",
                "en": "If you apply transformation A followed immediately by A inverse, every vector stays exactly where it began. In mathematics, this is the identity transformation.",
                "formula": "A^{-1} A = I = \\begin{bmatrix} 1 & 0 \\\\ 0 & 1 \\end{bmatrix}",
                "duration_ms": 16500.0
            },
            {
                "index": 5,
                "type": "insight-box",
                "text": "অতএব এ গুণ এক্স সমান ভি সমীকরণটি সমাধানের জন্য আমাদের কেবল উভয় পাশে এ ইনভার্স প্রয়োগ করতে হবে। ফলে আমরা এক নিমেষেই পেয়ে যাই: এক্স সমান এ ইনভার্স গুণ ভি!",
                "en": "Therefore, to solve A times x equals v, we simply apply A inverse to both sides of the equation, immediately yielding x equals A inverse times v!",
                "formula": "A\\vec{x} = \\vec{v} \\implies \\vec{x} = A^{-1}\\vec{v}",
                "duration_ms": 15200.0
            },
            {
                "index": 6,
                "type": "h3",
                "text": "ডিটারমিন্যান্ট শূন্য হলে কেন বিপরীত ম্যাট্রিক্স থাকতে পারে না?",
                "en": "Why can there be no inverse when the determinant is zero?",
                "formula": None,
                "duration_ms": 4600.0
            },
            {
                "index": 7,
                "type": "p",
                "text": "কিন্তু যদি ডিটারমিন্যান্ট শূন্য হয়, তখন কী ঘটবে? ডিটারমিন্যান্ট শূন্য মানে রূপান্তরটি পুরো দ্বিমাত্রিক সমতলকে চ্যাপ্টা করে একটি একমাত্রিক সরলরেখায় বা একক বিন্দুতে পরিণত করেছে।",
                "en": "What happens if the determinant is zero? A zero determinant means the transformation squished the entire 2D plane into a 1D line or a single point.",
                "formula": "\\det(A) = 0",
                "duration_ms": 13900.0
            },
            {
                "index": 8,
                "type": "figure",
                "text": "একমাত্রিক রেখাকে টেনে আবার দ্বিমাত্রিক সমতলে ফিরিয়ে আনার কোনো একক রূপান্তর তৈরি করা অসম্ভব! কারণ একটি রেখার একক বিন্দুকে সমতলের অসংখ্য বিন্দুতে ম্যাপিং করতে হবে, যা কোনো বৈধ ফাংশনের নিয়ম মানে না।",
                "en": "It is impossible to un-squish a 1D line back into a 2D plane with a single transformation, because an individual point on the line would have to map to an entire line of points, violating the definition of a function.",
                "formula": None,
                "duration_ms": 16800.0
            },
            {
                "index": 9,
                "type": "p",
                "text": "এই কারণেই যখন ডিটারমিন্যান্ট শূন্য হয়, তখন ম্যাট্রিক্সটির কোনো ইনভার্স বা বিপরীত ম্যাট্রিক্স থাকতে পারে না।",
                "en": "This is precisely why, whenever the determinant is zero, the matrix has no inverse.",
                "formula": "\\det(A) = 0 \\implies A^{-1} \\text{ does not exist}",
                "duration_ms": 9500.0
            }
        ]
    },
    {
        "section_id": "sec_03_rank_and_column_space",
        "title": "র‍্যাংক এবং কলাম স্পেস: রূপান্তরের সম্ভাব্য আউটপুট ক্ষেত্র",
        "title_en": "Rank and Column Space",
        "audio_file": "sec_03_rank_and_column_space.mp3",
        "cues_file": "sec_03_rank_and_column_space_cues.json",
        "summary_bn": "রূপান্তরের পর সমস্ত সম্ভাব্য আউটপুট ভেক্টরের সেট হলো কলাম স্পেস, এবং এর মাত্রাকে বলা হয় ম্যাট্রিক্সের র‍্যাংক।",
        "key_takeaways": [
            "কলাম স্পেস ($\\text{Col}(A)$) হলো রূপান্তর প্রয়োগের পর প্রাপ্ত সমস্ত আউটপুট ভেক্টর $A\\vec{v}$-এর সমগ্র বিস্তার।",
            "যেহেতু ম্যাট্রিক্সের কলামগুলো ভিত্তি ভেক্টরের রূপান্তরিত অবস্থান প্রকাশ করে, তাই কলাম স্পেস হলো ম্যাট্রিক্সের কলামগুলোর স্প্যান (Span)।",
            "র‍্যাংক হলো এই আউটপুট কলাম স্পেসের মাত্রা (Dimension): আউটপুট রেখা হলে র‍্যাংক ১, সমতল হলে র‍্যাংক ২, পূর্ণ ত্রিমাত্রিক আয়তন হলে র‍্যাংক ৩।",
            "র‍্যাংক কলাম সংখ্যার সমান হলে তাকে ফুল র‍্যাংক (Full Rank) বলা হয়।"
        ],
        "formulas": [
            {
                "label": "কলাম স্পেসের সংজ্ঞা",
                "katex": "\\text{Col}(A) = \\text{Span}(\\text{col}_1(A), \\text{col}_2(A), \\dots, \\text{col}_n(A))"
            },
            {
                "label": "র‍্যাংক ও কলাম স্পেসের মাত্রা",
                "katex": "\\text{Rank}(A) = \\dim(\\text{Col}(A))"
            },
            {
                "label": "ফুল র‍্যাংক শর্ত",
                "katex": "\\text{Full Rank} \\iff \\text{Rank}(A_{n \\times n}) = n \\iff \\det(A) \\neq 0"
            }
        ],
        "figures": [
            {
                "id": "fig_column_space_span",
                "caption_bn": "কলাম স্পেস হলো কলাম ভেক্টরগুলোর রৈখিক বিস্তার বা স্প্যান",
                "type": "svg",
                "src": "figures/column_space_span.svg"
            },
            {
                "id": "fig_rank_visual_dimensions",
                "caption_bn": "র‍্যাংক ১ (রেখা) বনাম র‍্যাংক ২ (সমতল) আউটপুট স্পেসের জ্যামিতিক রূপ",
                "type": "svg",
                "src": "figures/rank_visual_dimensions.svg"
            }
        ],
        "math_concepts": [
            "Column space: span of matrix columns",
            "Output space of transformation A*v",
            "Rank as dimension of the column space",
            "Rank 1 (line), Rank 2 (plane), Rank 3 (volume)",
            "Full rank condition"
        ],
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "text": "তৃতীয় পরিচ্ছেদ: র‍্যাংক এবং কলাম স্পেসের জ্যামিতিক রূপ।",
                "en": "Chapter 3: The Geometry of Rank and Column Space.",
                "formula": None,
                "duration_ms": 4300.0
            },
            {
                "index": 1,
                "type": "p",
                "text": "যখন কোনো রূপান্তরের মাধ্যমে সমতল চ্যাপ্টা হয়ে যায়, তখন তার আউটপুট ঠিক কেমন হতে পারে? রূপান্তর প্রয়োগ করার পর যত সম্ভাব্য আউটপুট ভেক্টর তৈরি হতে পারে, তাদের সমগ্র সেটকে বলা হয় কলাম স্পেস।",
                "en": "When a transformation squishes space, what does the output look like? The set of all possible outputs that a transformation can give is called the column space of the matrix.",
                "formula": "\\text{Col}(A) = \\{ A\\vec{v} : \\vec{v} \\in \\mathbb{R}^n \\}",
                "duration_ms": 16200.0
            },
            {
                "index": 2,
                "type": "p",
                "text": "কিন্তু এটিকে কলাম স্পেস নাম দেওয়া হলো কেন? কারণ আমরা জানি ম্যাট্রিক্সের প্রতিটি কলাম আসলে রূপান্তরের পর বেসিস ভেক্টরগুলো কোথায় গিয়ে পৌঁছায় তা নির্দেশ করে।",
                "en": "Why is it called the column space? Because the columns of a matrix tell you where the standard basis vectors land after the transformation.",
                "formula": None,
                "duration_ms": 11800.0
            },
            {
                "index": 3,
                "type": "insight-box",
                "text": "আর যেকোনো ভেক্টরের রূপান্তর হলো ওই কলামগুলোরই একটি রৈখিক সমাবেশ বা লিনিয়ার কম্বিনেশন! সুতরাং কলাম স্পেসের সহজ অর্থ হলো: ম্যাট্রিক্সের কলামগুলোর স্প্যান বা বিস্তার।",
                "en": "Every transformed vector is simply a linear combination of those transformed basis vectors! Thus, the column space is literally the span of the columns of the matrix.",
                "formula": "\\text{Column Space} = \\text{Span}(\\text{Columns of } A)",
                "duration_ms": 14900.0
            },
            {
                "index": 4,
                "type": "h3",
                "text": "র‍্যাংক: আউটপুট স্পেসের প্রকৃত মাত্রা।",
                "en": "Rank: The True Dimension of Output Space.",
                "formula": None,
                "duration_ms": 3600.0
            },
            {
                "index": 5,
                "type": "p",
                "text": "রূপান্তরের পর এই আউটপুট স্পেসের মাত্রা বা ডাইমেনশন কত—তা নির্দেশ করার গাণিতিক পরিমাপটির নামই হলো র‍্যাংক।",
                "en": "The dimension of this output space is called the rank of the transformation.",
                "formula": "\\text{Rank}(A) = \\dim(\\text{Col}(A))",
                "duration_ms": 10500.0
            },
            {
                "index": 6,
                "type": "figure",
                "text": "যদি আউটপুট একটি একমাত্রিক সরলরেখা হয়, তবে ম্যাট্রিক্সের র‍্যাংক হলো এক। আর যদি আউটপুটটি পুরো দ্বিমাত্রিক সমতল জুড়েই বিস্তৃত থাকে, তবে তার র‍্যাংক হলো দুই।",
                "en": "If the output is compressed into a one-dimensional line, the rank is 1. If the output fills the entire two-dimensional plane, the rank is 2.",
                "formula": "\\text{Line} \\implies \\text{Rank 1}, \\quad \\text{Plane} \\implies \\text{Rank 2}",
                "duration_ms": 13800.0
            },
            {
                "index": 7,
                "type": "p",
                "text": "ত্রিমাত্রিক স্থানে যদি আউটপুট স্থান সংকুচিত না হয়ে পূর্ণ থ্রিডি স্পেস থাকে, তবে র‍্যাংক তিন। আর যখন র‍্যাংক ম্যাট্রিক্সের কলাম সংখ্যার সমান হয়, তখন তাকে আমরা বলি ফুল র‍্যাংক।",
                "en": "In 3D, if the output is not compressed and occupies full 3D space, the rank is 3. When the rank equals the number of columns, the matrix is said to be full rank.",
                "formula": "\\text{Full Rank} \\iff \\text{Rank}(A) = n",
                "duration_ms": 13900.0
            }
        ]
    },
    {
        "section_id": "sec_04_null_space",
        "title": "নাল স্পেস বা শূন্য স্পেস: মূলবিন্দুতে সংকুচিত ভেক্টরের জগৎ",
        "title_en": "The Null Space (Kernel) and Solution Geometry",
        "audio_file": "sec_04_null_space.mp3",
        "cues_file": "sec_04_null_space_cues.json",
        "summary_bn": "মাত্রা সংকোচনের ফলে যেসব ভেক্টর শূন্য ভেক্টরে পতিত হয় তাদের সেটই হলো নাল স্পেস, যা সমীকরণ সমাধানের স্বাধীনতা নির্দেশ করে।",
        "key_takeaways": [
            "নাল স্পেস বা শূন্য স্পেস ($\\text{Null}(A)$ বা Kernel) হলো সমস্ত ইনপুট ভেক্টর $\\vec{x}$-এর সেট যা রূপান্তরের পর মূলবিন্দুতে সংকুচিত হয়: $A\\vec{x} = \\vec{0}$।",
            "দ্বিমাত্রিক স্থান সরলরেখায় সংকুচিত হলে একটি সম্পূর্ণ সরলরেখার সমস্ত ভেক্টর মূলবিন্দুতে গিয়ে মিশে যায়।",
            "যদি $A\\vec{x} = \\vec{v}$-এর একটি নির্দিষ্ট সমাধান $\\vec{x}_0$ থাকে, তবে $\\vec{x}_0$ এর সাথে নাল স্পেসের যেকোনো ভেক্টর $\\vec{n}$ যোগ করলেও তা বৈধ সমাধান হবে: $A(\\vec{x}_0 + \\vec{n}) = \\vec{v}$।",
            "র‍্যাংক-নালিটি উপপাদ্য (Rank-Nullity Theorem): ইনপুট মাত্রা = র‍্যাংক + নালিটি।"
        ],
        "formulas": [
            {
                "label": "নাল স্পেস বা কার্নেল সংজ্ঞা",
                "katex": "\\text{Null}(A) = \\ker(A) = \\{ \\vec{x} \\in \\mathbb{R}^n : A\\vec{x} = \\vec{0} \\}"
            },
            {
                "label": "সাধারণ সমাধান ও নাল স্পেস অফসেট",
                "katex": "A\\vec{x} = \\vec{v} \\implies \\vec{x} = \\vec{x}_p + \\vec{x}_n, \\quad \\vec{x}_n \\in \\text{Null}(A)"
            },
            {
                "label": "র‍্যাংক-নালিটি উপপাদ্য",
                "katex": "\\text{Rank}(A) + \\text{Nullity}(A) = n \\quad (\\text{Dimension of Input Space})"
            }
        ],
        "figures": [
            {
                "id": "fig_null_space_collapse",
                "caption_bn": "সমতলের একটি সম্পূর্ণ সরলরেখা সংকুচিত হয়ে মূলবিন্দুতে পতিত হচ্ছে",
                "type": "svg",
                "src": "figures/null_space_collapse.svg"
            },
            {
                "id": "fig_solution_line_offset",
                "caption_bn": "নাল স্পেসের সমান্তরাল রেখা বরাবর সমাধানের বিস্তার",
                "type": "svg",
                "src": "figures/solution_line_offset.svg"
            }
        ],
        "math_concepts": [
            "Null space / Kernel definition: Ax = 0",
            "Dimensional collapse mapping vectors to origin",
            "Line of vectors collapsed to origin in 2D",
            "General solution: x = x_p + x_n (null space offset)",
            "Rank-Nullity theorem intuition"
        ],
        "cues": [
            {
                "index": 0,
                "type": "h2",
                "text": "চতুর্থ পরিচ্ছেদ: নাল স্পেস বা শূন্য স্পেস এবং সমাধানের জ্যামিতি।",
                "en": "Chapter 4: The Null Space (Kernel) and the Geometry of Solutions.",
                "formula": None,
                "duration_ms": 4800.0
            },
            {
                "index": 1,
                "type": "p",
                "text": "যখন কোনো রৈখিক রূপান্তরের ডিটারমিন্যান্ট শূন্য হয় এবং সমতল সংকুচিত হয়ে একটি সরলরেখায় পরিণত হয়, তখন মূলবিন্দু ছাড়াও অসংখ্য ভেক্টর নিশ্চয়ই মূলবিন্দুর ওপর গিয়ে আছড়ে পড়ে।",
                "en": "When a linear transformation squishes space into a line (det = 0), then besides the origin, a whole bunch of other vectors must land squarely on the origin as well.",
                "formula": None,
                "duration_ms": 14700.0
            },
            {
                "index": 2,
                "type": "figure",
                "text": "পাশের অ্যানিমেশনে লক্ষ্য করুন: সমতলের একটি সম্পূর্ণ সরলরেখায় অবস্থিত সমস্ত ভেক্টর রূপান্তরের পর সংকুচিত হয়ে মূলবিন্দু শূন্যে গিয়ে মিলিত হচ্ছে।",
                "en": "In the animation, watch how an entire line of vectors in the 2D plane collapses directly into the origin under the transformation.",
                "formula": None,
                "duration_ms": 12500.0
            },
            {
                "index": 3,
                "type": "formula-box",
                "text": "যে সমস্ত ইনপুট ভেক্টর রূপান্তরের পর সরাসরি মূলবিন্দু বা শূন্য ভেক্টরে পরিণত হয়, তাদের সমগ্র সেটকে বলা হয় ওই ম্যাট্রিক্সের নাল স্পেস বা শূন্য স্পেস। একে অনেকে কার্নেলও বলে থাকেন।",
                "en": "The set of all input vectors that end up landing on the origin is called the null space or kernel of the matrix.",
                "formula": "\\text{Null}(A) = \\{ \\vec{x} \\in \\mathbb{R}^n : A\\vec{x} = \\vec{0} \\}",
                "duration_ms": 17200.0
            },
            {
                "index": 4,
                "type": "insight-box",
                "text": "সমীকরণ জোট সমাধানের ক্ষেত্রে নাল স্পেসের ভূমিকা অত্যন্ত গুরুত্বপূর্ণ। যদি এ গুণ এক্স সমান ভি সমীকরণের একটি নির্দিষ্ট সমাধান এক্স নট থাকে, তবে এক্স নটের সাথে নাল স্পেসের যেকোনো ভেক্টর যোগ করলেও তা একটি সম্পূর্ণ নির্ভুল সমাধান দেবে!",
                "en": "When solving systems of equations, the null space plays a crucial role. If you have a specific solution x_0 to Ax = v, adding any vector from the null space to x_0 produces another valid solution!",
                "formula": "A(\\vec{x}_0 + \\vec{n}) = A\\vec{x}_0 + A\\vec{n} = \\vec{v} + \\vec{0} = \\vec{v}",
                "duration_ms": 20100.0
            },
            {
                "index": 5,
                "type": "p",
                "text": "কারণ নাল স্পেসের ভেক্টর রূপান্তরের পর শূন্য হয়ে যায়, তাই এটি ফলাফলে কোনো হেরফের ঘটায় না। অর্থাৎ নাল স্পেস আমাদের সমাধানের সম্পূর্ণ জ্যামিতিক ক্ষেত্র ও স্বাধীনতার মাত্রা উপহার দেয়।",
                "en": "Because vectors in the null space map to zero, adding them changes nothing about the output. Thus, the null space tells you the full geometric freedom of solutions.",
                "formula": None,
                "duration_ms": 14500.0
            },
            {
                "index": 6,
                "type": "p",
                "text": "এই গভীর উপলব্ধিটি আমাদের স্পষ্ট করে দেয়: লিনিয়ার অ্যালজেব্রায় বিপরীত ম্যাট্রিক্স, কলাম স্পেস এবং নাল স্পেস কোনো বিচ্ছিন্ন সূত্র নয়—বরং এরা স্থানকে রূপান্তর ও সংকোচনের এক অবিচ্ছেদ্য এবং সুসংহত জ্যামিতিক গল্প!",
                "en": "This profound realization shows that inverse matrices, column space, and null space are not isolated formulas, but a unified geometric narrative of how transformations warp space.",
                "formula": None,
                "duration_ms": 16900.0
            }
        ]
    }
]

# Calculate timing
for sec in SECTIONS_DATA:
    curr_t = 0.0
    for cue in sec["cues"]:
        dur = cue["duration_ms"]
        cue["start_ms"] = round(curr_t, 1)
        cue["end_ms"] = round(curr_t + dur, 1)
        curr_t += dur + 350.0
    sec["total_duration_ms"] = round(curr_t, 1)

# Build Master Script JSON
master_script_data = {
    "course_id": "linear_algebra",
    "lesson_id": "lesson_07",
    "title_en": "Inverse matrices, column space and null space",
    "title_bn": "বিপরীত ম্যাট্রিক্স, কলাম স্পেস ও শূন্য স্পেস",
    "video_id": "uQhTuRlWM3E",
    "source_url": "https://www.3blue1brown.com/lessons/inverse-matrices",
    "voice_standard": {
        "engine": "Edge-TTS / Natural Native Educator",
        "voice": "bn-BD-PradeepNeural",
        "phonetic_rules": [
            "AI -> এআই",
            "2D -> টুডি",
            "3D -> থ্রিডি",
            "x-axis -> এক্স অক্ষ",
            "y-axis -> ওয়াই অক্ষ",
            "z-axis -> জেড অক্ষ",
            "x -> এক্স",
            "y -> ওয়াই",
            "z -> জেড",
            "i-hat -> আই হ্যাট",
            "j-hat -> জে হ্যাট",
            "k-hat -> কে হ্যাট",
            "A -> এ",
            "A^(-1) -> এ ইনভার্স",
            "v -> ভি",
            "x -> এক্স",
            "det -> ডিটারমিন্যান্ট",
            "null space -> নাল স্পেস বা শূন্য স্পেস",
            "column space -> কলাম স্পেস",
            "rank -> র‍্যাংক"
        ]
    },
    "sections": SECTIONS_DATA
}

with open(MASTER_SCRIPT_FILE, "w", encoding="utf-8") as f:
    json.dump(master_script_data, f, ensure_ascii=False, indent=2)
print(f"Master script written: {MASTER_SCRIPT_FILE}")

# Build Audio Manifest JSON & JS
sections_manifest = {}
for sec in SECTIONS_DATA:
    sec_id = sec["section_id"]
    # Write individual cues file
    cue_file_path = AUDIO_DIR / sec["cues_file"]
    sec_cue_data = {
        "section_id": sec_id,
        "title": sec["title"],
        "audio_file": sec["audio_file"],
        "total_duration_ms": sec["total_duration_ms"],
        "cues": sec["cues"]
    }
    with open(cue_file_path, "w", encoding="utf-8") as f:
        json.dump(sec_cue_data, f, ensure_ascii=False, indent=2)
    
    sections_manifest[sec_id] = {
        "title": sec["title"],
        "audio_file": sec["audio_file"],
        "cues_file": sec["cues_file"],
        "total_duration_ms": sec["total_duration_ms"],
        "cues": sec["cues"]
    }

audio_manifest_obj = {
    "course": "linear_algebra",
    "lesson": "lesson_07",
    "voice": "bn-BD-PradeepNeural",
    "mode": "authentic_teacher",
    "sections": sections_manifest
}

with open(AUDIO_MANIFEST_JSON, "w", encoding="utf-8") as f:
    json.dump(audio_manifest_obj, f, ensure_ascii=False, indent=2)
print(f"Audio manifest written: {AUDIO_MANIFEST_JSON}")

manifest_js_content = f"window.TEACHER_AUDIO_MANIFEST = {json.dumps(audio_manifest_obj, ensure_ascii=False, indent=2)};\n"
with open(AUDIO_MANIFEST_JS, "w", encoding="utf-8") as f:
    f.write(manifest_js_content)
print(f"Audio manifest JS written: {AUDIO_MANIFEST_JS}")

# Build Single-Shell Lesson Data JSON (lesson_07.json)
quizzes_data = [
    {
        "id": "quiz_01_linear_system_geometry",
        "section_ref": "sec_01_linear_systems",
        "question_bn": "একটি রৈখিক সমীকরণ জোট $A\\vec{x} = \\vec{v}$-এর জ্যামিতিক তাৎপর্য কী?",
        "question_en": "What is the geometric meaning of solving a linear system Ax = v?",
        "options": [
            "শুধুমাত্র সারি ও কলামের স্কেলার মান বিনিময় করা",
            "এমন একটি আদি ভেক্টর $\\vec{x}$ খুঁজে বের করা, যা $A$ রূপান্তরের পর $\\vec{v}$-এর ওপর গিয়ে পড়ে",
            "ম্যাট্রিক্স $A$-এর কর্ণের উপাদানগুলোর গুণফল নির্ণয় করা",
            "ভেক্টর $\\vec{v}$-কে সমতলে ৯০ ডিগ্রি কোণে ঘুরিয়ে দেওয়া"
        ],
        "correct_index": 1,
        "explanation_bn": "জ্যামিতিক দৃষ্টিকোণ থেকে সমীকরণ জোট সমাধানের আসল অর্থ হলো এমন একটি ইনপুট ভেক্টর $\\vec{x}$ সন্ধান করা, যার ওপর ম্যাট্রিক্স রূপান্তর $A$ প্রয়োগ করলে তা ঠিক টার্গেট ভেক্টর $\\vec{v}$-তে রূপান্তরিত হয়।",
        "explanation_en": "Geometrically, solving Ax = v means finding the input vector x that lands on vector v after transformation A is applied."
    },
    {
        "id": "quiz_02_inverse_existence",
        "section_ref": "sec_02_inverse_matrices",
        "question_bn": "কোন শর্তে কোনো ম্যাট্রিক্স $A$-এর বিপরীত ম্যাট্রিক্স $A^{-1}$ নিশ্চিতভাবে বিদ্যমান থাকে?",
        "question_en": "Under what condition does the inverse matrix A^(-1) exist?",
        "options": [
            "ম্যাট্রিক্সটির ডিটারমিন্যান্ট শূন্য হলে $(\\det(A) = 0)$",
            "ম্যাট্রিক্সটির ডিটারমিন্যান্ট অশূন্য হলে $(\\det(A) \\neq 0)$",
            "ম্যাট্রিক্সের সমস্ত উপাদান ধনাত্মক হলে",
            "ম্যাট্রিক্সটির ট্রেস শূন্য হলে"
        ],
        "correct_index": 1,
        "explanation_bn": "যদি $\\det(A) \\neq 0$ হয়, তবে স্থান সংকুচিত হয় না। ফলে পুরো রূপান্তরটিকে আবার উল্টো দিকে চালিয়ে আদি অবস্থায় ফিরিয়ে আনা সম্ভব হয়, অর্থাৎ বিপরীত ম্যাট্রিক্স $A^{-1}$ বিদ্যমান থাকে।",
        "explanation_en": "When det(A) != 0, space is not squished into a lower dimension, making the transformation fully reversible."
    },
    {
        "id": "quiz_03_rank_meaning",
        "section_ref": "sec_03_rank_and_column_space",
        "question_bn": "একটি ৩×৩ ম্যাট্রিক্সের ক্ষেত্রে রূপান্তরের পর সমস্ত আউটপুট ভেক্টর একটি দ্বিমাত্রিক সমতলে সীমাবদ্ধ থাকলে ম্যাট্রিক্সটির র‍্যাংক কত?",
        "question_en": "For a 3x3 matrix, if all output vectors land on a 2D plane, what is its rank?",
        "options": [
            "০",
            "১",
            "২",
            "৩"
        ],
        "correct_index": 2,
        "explanation_bn": "র‍্যাংক হলো কলাম স্পেস বা আউটপুট স্থানের প্রকৃত মাত্রা। যেহেতু সমস্ত আউটপুট ভেক্টর একটি দ্বিমাত্রিক সমতল (2D plane) গঠন করে, তাই উক্ত রূপান্তরের র‍্যাংক হলো ২।",
        "explanation_en": "Rank is the dimension of the column space (output space). Since the outputs form a 2D plane, the rank is 2."
    },
    {
        "id": "quiz_04_null_space_property",
        "section_ref": "sec_04_null_space",
        "question_bn": "ম্যাট্রিক্সের নাল স্পেস (Null Space বা Kernel) বলতে কী বোঝায়?",
        "question_en": "What is the null space (kernel) of a matrix?",
        "options": [
            "যে সমস্ত ভেক্টরের দৈর্ঘ্য এক একক",
            "যে সমস্ত ইনপুট ভেক্টর রূপান্তরের পর মূলবিন্দু বা শূন্য ভেক্টরে $(\\vec{0})$ পরিণত হয়",
            "ম্যাট্রিক্সের প্রধান কর্ণের বাইরে অবস্থিত উপাদানগুলো",
            "যেসব ভেক্টর রূপান্তরের পরও সম্পূর্ণ অপরিবর্তিত থাকে"
        ],
        "correct_index": 1,
        "explanation_bn": "যে সমস্ত ভেক্টর $\\vec{x}$-এর ওপর রূপান্তর $A$ প্রয়োগ করলে ফলাফল সরাসরি শূন্য ভেক্টর পাওয়া যায় ($A\\vec{x} = \\vec{0}$), তাদের সমগ্র সেটকে বলা হয় নাল স্পেস বা কার্নেল।",
        "explanation_en": "The null space is the set of all input vectors x that map to the zero vector (Ax = 0)."
    }
]

lesson_json_data = {
    "lesson_id": "lesson_07",
    "chapter_num": 7,
    "course_id": "linear_algebra",
    "title_en": "Inverse matrices, column space and null space",
    "title_bn": "বিপরীত ম্যাট্রিক্স, কলাম স্পেস ও শূন্য স্পেস",
    "subtitle_bn": "রৈখিক সমীকরণ জোটের সমাধান, বিপরীত রূপান্তর এবং মাত্রা সংকোচনের জ্যামিতিক রহস্য",
    "video_id": "uQhTuRlWM3E",
    "official_url": "https://www.3blue1brown.com/lessons/inverse-matrices",
    "meta": {
        "credits": "Grant Sanderson (3Blue1Brown)",
        "translator_curator": "Bengali STEM Pedagogy Unit",
        "duration": "12:09",
        "prerequisites": [
            "lesson_03",
            "lesson_04",
            "lesson_05",
            "lesson_06"
        ]
    },
    "epigraph": {
        "quote": "To invert a matrix is to run time backwards, recovering where every vector stood before the transformation warped the space.",
        "quote_bn": "ম্যাট্রিক্সকে বিপরীত করা মানে সময়কে উল্টো দিকে চালানো—স্থানটি বিকৃত হওয়ার পূর্বে প্রতিটি ভেক্টর ঠিক কোথায় দাঁড়িয়েছিল তা পুনরুদ্ধার করা।",
        "author": "Grant Sanderson"
    },
    "sections": [
        {
            "id": sec["section_id"],
            "title_bn": f"{i+1}. {sec['title']}",
            "title_en": sec["title_en"],
            "summary_bn": sec["summary_bn"],
            "key_takeaways": sec["key_takeaways"],
            "formulas": sec["formulas"],
            "figures": sec["figures"],
            "interactive_widget": sec.get("interactive_widget", None)
        }
        for i, sec in enumerate(SECTIONS_DATA)
    ],
    "quizzes": quizzes_data
}

with open(LESSON_DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(lesson_json_data, f, ensure_ascii=False, indent=2)
print(f"Lesson data JSON written: {LESSON_DATA_FILE}")

print("All Lesson 07 resources created successfully!")

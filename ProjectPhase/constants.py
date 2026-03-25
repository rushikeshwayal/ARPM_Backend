# ─────────────────────────────────────────────────────────────────────────────
# PREDEFINED PHASES
# These are seeded automatically when the first tranche is released.
# ─────────────────────────────────────────────────────────────────────────────

PREDEFINED_PHASES = [
    {
        "phase_number": 1,
        "phase_name":   "Problem & Literature",
        "description":  "Define the research problem, review literature, identify gaps, establish baselines and success metrics.",
    },
    {
        "phase_number": 2,
        "phase_name":   "Hypothesis & Planning",
        "description":  "Form hypotheses, design experiments, plan data collection, define evaluation framework.",
    },
    {
        "phase_number": 3,
        "phase_name":   "Experimentation",
        "description":  "Execute experiments, collect data, run models, log results.",
    },
    {
        "phase_number": 4,
        "phase_name":   "Evaluation & Analysis",
        "description":  "Analyse results, compare against baselines, document findings.",
    },
    {
        "phase_number": 5,
        "phase_name":   "Reporting & Deployment",
        "description":  "Write final report, prepare deployment artifacts, submit deliverables.",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# PREDEFINED STEPS PER PHASE
# Steps are sequential and locked — must be completed in order.
# ─────────────────────────────────────────────────────────────────────────────

PHASE_STEPS = {

    # ── Phase 1: Problem & Literature ────────────────────────────────────────
    1: [
        {
            "step_number": 1,
            "step_name":   "Define Problem",
            "description": "Write a clear problem statement, scope, and motivation.",
        },
        {
            "step_number": 2,
            "step_name":   "Add Papers",
            "description": "Add relevant research papers and summarise key findings.",
        },
        {
            "step_number": 3,
            "step_name":   "Identify Research Gap",
            "description": "Identify what is missing or unsolved in existing literature.",
        },
        {
            "step_number": 4,
            "step_name":   "Define Baselines",
            "description": "List the baseline models or methods to compare against.",
        },
        {
            "step_number": 5,
            "step_name":   "Define Success Metrics",
            "description": "Define measurable criteria for success (accuracy, F1, latency, etc.).",
        },
    ],

    # ── Phase 2: Hypothesis & Planning ───────────────────────────────────────
    2: [
        {
            "step_number": 1,
            "step_name":   "Form Hypotheses",
            "description": "State testable hypotheses grounded in Phase 1 findings.",
        },
        {
            "step_number": 2,
            "step_name":   "Design Experiments",
            "description": "Design controlled experiments to test each hypothesis.",
        },
        {
            "step_number": 3,
            "step_name":   "Data Collection Plan",
            "description": "Define data sources, collection methods, and preprocessing steps.",
        },
        {
            "step_number": 4,
            "step_name":   "Resource & Timeline Plan",
            "description": "Map compute resources, team assignments, and milestones.",
        },
    ],

    # ── Phase 3: Experimentation ─────────────────────────────────────────────
    3: [
        {
            "step_number": 1,
            "step_name":   "Data Collection & Preprocessing",
            "description": "Collect, clean, and prepare datasets for training.",
        },
        {
            "step_number": 2,
            "step_name":   "Model Development",
            "description": "Build, configure, and implement the proposed model(s).",
        },
        {
            "step_number": 3,
            "step_name":   "Training & Iteration",
            "description": "Train models, tune hyperparameters, log experiments.",
        },
        {
            "step_number": 4,
            "step_name":   "Results Logging",
            "description": "Record all experiment results with reproducibility details.",
        },
    ],

    # ── Phase 4: Evaluation & Analysis ───────────────────────────────────────
    4: [
        {
            "step_number": 1,
            "step_name":   "Evaluate Against Baselines",
            "description": "Compare model performance with baselines from Phase 1.",
        },
        {
            "step_number": 2,
            "step_name":   "Error Analysis",
            "description": "Analyse failure modes, edge cases, and model weaknesses.",
        },
        {
            "step_number": 3,
            "step_name":   "Document Findings",
            "description": "Summarise evaluation outcomes and conclusions.",
        },
    ],

    # ── Phase 5: Reporting & Deployment ─────────────────────────────────────
    5: [
        {
            "step_number": 1,
            "step_name":   "Final Report",
            "description": "Write comprehensive research report.",
        },
        {
            "step_number": 2,
            "step_name":   "Deployment Artifacts",
            "description": "Package model, API, or deliverable for deployment.",
        },
        {
            "step_number": 3,
            "step_name":   "Handover & Closure",
            "description": "Submit final deliverables, close project.",
        },
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT TYPES PER STEP
# Required / optional documents for each step.
# format: { phase_number: { step_number: [ {type, label, required} ] } }
# ─────────────────────────────────────────────────────────────────────────────

STEP_DOCUMENT_TYPES = {

    1: {  # Phase 1
        1: [  # Define Problem
            {"type": "problem_statement",  "label": "Problem Statement Doc",  "required": True  },
            {"type": "scope_document",     "label": "Scope Document",         "required": False },
        ],
        2: [  # Add Papers
            {"type": "literature_survey",  "label": "Literature Survey",      "required": True  },
            {"type": "paper_summary",      "label": "Paper Summary Sheet",    "required": False },
            {"type": "reference_list",     "label": "Reference List",         "required": False },
        ],
        3: [  # Identify Research Gap
            {"type": "gap_analysis",       "label": "Research Gap Analysis",  "required": True  },
        ],
        4: [  # Define Baselines
            {"type": "baseline_doc",       "label": "Baseline Definition Doc","required": True  },
        ],
        5: [  # Define Success Metrics
            {"type": "metrics_doc",        "label": "Success Metrics Doc",    "required": True  },
            {"type": "evaluation_plan",    "label": "Evaluation Plan",        "required": False },
        ],
    },

    2: {  # Phase 2
        1: [
            {"type": "hypothesis_doc",     "label": "Hypothesis Document",    "required": True  },
        ],
        2: [
            {"type": "experiment_design",  "label": "Experiment Design Doc",  "required": True  },
        ],
        3: [
            {"type": "data_plan",          "label": "Data Collection Plan",   "required": True  },
            {"type": "data_sample",        "label": "Sample Dataset",         "required": False },
        ],
        4: [
            {"type": "resource_plan",      "label": "Resource Plan",          "required": True  },
            {"type": "timeline_doc",       "label": "Timeline Document",      "required": False },
        ],
    },

    3: {  # Phase 3
        1: [
            {"type": "dataset_doc",        "label": "Dataset Documentation",  "required": True  },
            {"type": "preprocessing_code", "label": "Preprocessing Script",   "required": False },
        ],
        2: [
            {"type": "model_architecture", "label": "Model Architecture Doc", "required": True  },
            {"type": "code_repo_link",     "label": "Code Repository Link",   "required": False },
        ],
        3: [
            {"type": "training_log",       "label": "Training Log",           "required": True  },
            {"type": "hyperparameter_doc", "label": "Hyperparameter Report",  "required": False },
        ],
        4: [
            {"type": "results_sheet",      "label": "Results Sheet",          "required": True  },
            {"type": "experiment_log",     "label": "Experiment Log",         "required": False },
        ],
    },

    4: {  # Phase 4
        1: [
            {"type": "evaluation_report",  "label": "Evaluation Report",      "required": True  },
            {"type": "comparison_table",   "label": "Comparison Table",       "required": False },
        ],
        2: [
            {"type": "error_analysis_doc", "label": "Error Analysis",         "required": True  },
        ],
        3: [
            {"type": "findings_report",    "label": "Findings Report",        "required": True  },
        ],
    },

    5: {  # Phase 5
        1: [
            {"type": "final_report",       "label": "Final Research Report",  "required": True  },
        ],
        2: [
            {"type": "deployment_package", "label": "Deployment Package",     "required": True  },
            {"type": "api_documentation",  "label": "API Documentation",      "required": False },
        ],
        3: [
            {"type": "handover_doc",       "label": "Handover Document",      "required": True  },
            {"type": "closure_report",     "label": "Project Closure Report", "required": True  },
        ],
    },
}

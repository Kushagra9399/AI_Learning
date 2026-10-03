QP = {
    "qp_code": "CON/Q0603",
    "name": "Construction Electrician - LV",
    "version": "5.0",
    "nsqf_level": 4,
    "pass_percentage": 70,
    "total_marks": 650,
    "theory_marks": 200,
    "practical_marks": 450,
    "source_url": "https://s3.ap-south-1.amazonaws.com/nsdcproddocuments/qpPdf/CON_Q0603_v5.0.pdf",
    "assessment_note": "AI supports evidence organization and scoring assistance; an authorized assessor makes the final judgement.",
    "nos": [
        {"code":"CON/N0608","name":"Cable laying and construction-site equipment electrification","weightage":20,"pcs":[
            {"id":"PC1","description":"Interpret electrical drawings and work requirements."},
            {"id":"PC2","description":"Identify hazards and apply safe isolation."},
            {"id":"PC3","description":"Lay, route and terminate cables correctly."},
            {"id":"PC4","description":"Apply earthing and protective measures."},
            {"id":"PC5","description":"Carry out required electrical tests and record readings."}
        ]},
        {"code":"CON/N0609","name":"Electrical maintenance of construction equipment","weightage":20,"pcs":[
            {"id":"PC1","description":"Diagnose electrical faults systematically."},
            {"id":"PC2","description":"Follow safe testing and isolation procedures."},
            {"id":"PC3","description":"Carry out maintenance or replacement of rated parts."},
            {"id":"PC4","description":"Check earthing and protection."},
            {"id":"PC5","description":"Record test readings and maintenance actions."}
        ]},
        {"code":"CON/N0610","name":"LV electrical wiring and building electrification","weightage":20,"pcs":[
            {"id":"PC1","description":"Plan wiring work from drawings and requirements."},
            {"id":"PC2","description":"Install wiring, fixtures and fittings."},
            {"id":"PC3","description":"Complete earthing and protective connections."},
            {"id":"PC4","description":"Test circuits before energization."},
            {"id":"PC5","description":"Correct defects and leave the work area safe."}
        ]},
        {"code":"CON/N9001","name":"Health, safety and environment","weightage":10,"pcs":[
            {"id":"PC1","description":"Identify workplace hazards."},
            {"id":"PC2","description":"Use required PPE and safety controls."},
            {"id":"PC3","description":"Follow emergency and safe-work procedures."},
            {"id":"PC4","description":"Maintain housekeeping and waste controls."}
        ]},
        {"code":"CON/N8001","name":"Teamwork","weightage":10,"pcs":[
            {"id":"PC1","description":"Communicate work requirements clearly."},
            {"id":"PC2","description":"Coordinate with team members."},
            {"id":"PC3","description":"Resolve work issues constructively."}
        ]},
        {"code":"CON/N8002","name":"Plan and organize work","weightage":10,"pcs":[
            {"id":"PC1","description":"Sequence activities and estimate resources."},
            {"id":"PC2","description":"Organize tools and materials."},
            {"id":"PC3","description":"Complete assigned work within agreed time."}
        ]},
        {"code":"DGT/VSQ/N0101","name":"Employability Skills","weightage":10,"pcs":[
            {"id":"PC1","description":"Use professional communication."},
            {"id":"PC2","description":"Use digital tools and credentials safely."},
            {"id":"PC3","description":"Apply problem solving and time management."}
        ]}
    ]
}

THEORY_QUESTIONS = [
    {"id":"q-1","nos_code":"CON/N9001","pc_id":"PC2","question":"What should happen before electrical work begins?","options":["Ignore hazards","Complete safe isolation and required controls","Remove PPE","Energize first"],"correct_option":1},
    {"id":"q-2","nos_code":"CON/N0608","pc_id":"PC1","question":"What should an electrician use to understand the intended circuit arrangement before installation?","options":["Electrical drawing","Paint chart","Attendance sheet","Toolbox label"],"correct_option":0},
    {"id":"q-3","nos_code":"CON/N0608","pc_id":"PC5","question":"Which instrument is appropriate for measuring electrical voltage?","options":["Voltmeter/multimeter","Spirit level","Pipe wrench","Tape measure"],"correct_option":0},
    {"id":"q-4","nos_code":"CON/N0609","pc_id":"PC2","question":"What is appropriate before maintenance testing on electrical equipment?","options":["Increase the load","Follow safe isolation and testing precautions","Bypass protection","Remove warnings"],"correct_option":1},
    {"id":"q-5","nos_code":"CON/N0610","pc_id":"PC4","question":"What should be checked before energizing a newly wired circuit?","options":["Paint colour","Required wiring, continuity/insulation and safety tests","Phone battery","Nothing"],"correct_option":1},
    {"id":"q-6","nos_code":"CON/N0610","pc_id":"PC3","question":"What is the purpose of protective earthing?","options":["Improve decoration","Provide a safe fault-current path and reduce shock risk","Increase cable length","Replace all fuses"],"correct_option":1},
    {"id":"q-7","nos_code":"CON/N9001","pc_id":"PC1","question":"Which action is part of hazard identification?","options":["Starting without inspection","Identifying electrical and site hazards before work","Ignoring signage","Removing barriers"],"correct_option":1},
    {"id":"q-8","nos_code":"CON/N8001","pc_id":"PC2","question":"How should a workplace coordination issue be handled?","options":["Stop communication","Coordinate and resolve it constructively","Hide it","Blame someone"],"correct_option":1},
    {"id":"q-9","nos_code":"CON/N8002","pc_id":"PC1","question":"What should be planned before beginning a practical task?","options":["Tools, materials, sequence and resources","Nothing","Random start","Skip resource checks"],"correct_option":0},
    {"id":"q-10","nos_code":"DGT/VSQ/N0101","pc_id":"PC2","question":"Which is a safe digital practice?","options":["Share passwords","Protect credentials and use trusted systems","Disable security","Use unknown links"],"correct_option":1},
    {"id":"q-11","nos_code":"CON/N0609","pc_id":"PC1","question":"What is a useful first step when diagnosing an electrical fault?","options":["Replace every component","Gather symptoms and test systematically","Bypass the protection","Energize an unsafe circuit"],"correct_option":1},
    {"id":"q-12","nos_code":"CON/N0610","pc_id":"PC2","question":"What should an installer verify while fitting electrical accessories?","options":["Correct rating, connection and secure installation","Only colour","Only price","Nothing"],"correct_option":0}
]

PRACTICAL_TASKS = [
    {"id":"PT-01","title":"Safe isolation and hazard assessment","nos_code":"CON/N9001","pc_ids":["PC1","PC2","PC3"],"max_score":20,"evidence_required":True,
     "instructions":"Demonstrate how you would identify hazards and safely isolate an electrical work area before starting work.","safety":"Use a de-energized training setup. Do not expose a person to live electrical hazards.",
     "rubric":[{"criterion":"Hazard identification","weight":5},{"criterion":"PPE and safety controls","weight":5},{"criterion":"Isolation sequence","weight":5},{"criterion":"Clear communication/housekeeping","weight":5}]},
    {"id":"PT-02","title":"LV wiring and termination","nos_code":"CON/N0610","pc_ids":["PC1","PC2","PC3"],"max_score":25,"evidence_required":True,
     "instructions":"Using a safe training board, interpret the given wiring requirement, route conductors and make correct terminations.","safety":"Use an isolated training board and rated components; assessor controls energization.",
     "rubric":[{"criterion":"Interprets work requirement","weight":5},{"criterion":"Routing and identification","weight":5},{"criterion":"Termination quality","weight":10},{"criterion":"Earthing/protection awareness","weight":5}]},
    {"id":"PT-03","title":"Electrical testing before energization","nos_code":"CON/N0608","pc_ids":["PC4","PC5"],"max_score":20,"evidence_required":True,
     "instructions":"Demonstrate the test sequence you would use on a de-energized training circuit and explain the expected readings.","safety":"Testing is performed on an approved de-energized training circuit under assessor supervision.",
     "rubric":[{"criterion":"Selects appropriate test method","weight":5},{"criterion":"Uses instrument safely","weight":5},{"criterion":"Interprets readings","weight":5},{"criterion":"Records results and escalation","weight":5}]},
    {"id":"PT-04","title":"Fault diagnosis and maintenance plan","nos_code":"CON/N0609","pc_ids":["PC1","PC2","PC5"],"max_score":20,"evidence_required":True,
     "instructions":"Given a simulated equipment fault, explain and demonstrate a systematic diagnostic sequence and maintenance record.","safety":"Use a simulated fault or isolated training equipment only.",
     "rubric":[{"criterion":"Fault isolation approach","weight":5},{"criterion":"Safe testing sequence","weight":5},{"criterion":"Correct diagnosis/replacement decision","weight":5},{"criterion":"Maintenance record","weight":5}]},
    {"id":"PT-05","title":"Work planning and team coordination","nos_code":"CON/N8001","pc_ids":["PC1","PC2"],"max_score":15,"evidence_required":False,
     "instructions":"Plan a small electrical job, identify resources and explain how you would coordinate with another worker.","safety":"No live electrical work is required.",
     "rubric":[{"criterion":"Work sequence and resources","weight":5},{"criterion":"Communication and coordination","weight":5},{"criterion":"Time/quality planning","weight":5}]}
]

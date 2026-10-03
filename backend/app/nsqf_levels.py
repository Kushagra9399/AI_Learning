"""Detailed NSQF level descriptors used by the RPL assessment assistant.

Source basis: National Qualifications Register (NQR), "Level Descriptors for
NSQF Levels". The descriptors are learning-outcome based and cover theoretical
knowledge, professional/technical skills, aptitude/employability, broad
learning outcomes, and responsibility.

Certification note:
NSQF does not prescribe one universal certificate for a level. Qualification
and certification requirements are occupation/sector specific. The
certification guidance below therefore points to the type of qualification
evidence to verify rather than claiming that a particular certificate is
mandatory for every worker.
"""

NSQF_LEVEL_DESCRIPTORS = {
    1: {
        "title": "Foundation / Helper / Ground-Level Worker",
        "knowledge": [
            "Elementary knowledge of a familiar work area.",
            "Understands basic facts, terms, simple processes and workplace instructions.",
            "Knowledge is mainly practical and directly related to the assigned task.",
        ],
        "technical_skills": [
            "Uses narrow, basic skills for simple and familiar tasks.",
            "Follows standard operating instructions and basic safety practices.",
            "Uses basic tools, materials and equipment under close guidance.",
        ],
        "aptitude_employability": [
            "Basic workplace awareness and readiness to follow instructions.",
            "Can communicate simple work information and cooperate with others.",
            "Shows basic safety, discipline, attendance and work habits.",
        ],
        "learning_outcomes": [
            "Performs routine and repetitive tasks in a familiar setting.",
            "Recognises obvious problems and reports them rather than independently resolving them.",
            "Applies known procedures with limited variation.",
        ],
        "responsibility": [
            "Works mainly under continuous or close supervision.",
            "Has responsibility for completing assigned tasks safely and correctly.",
            "Acts as a helper or ground-level worker within a defined work process.",
        ],
        "typical_role": "Helper / Ground-Level Worker",
        "entry_and_training": "The descriptor framework generally associates Level 1 with no formal education and no prior experience; suggested short-term training is about 150–210 hours including employability skills.",
        "certification_guidance": [
            "Look for an occupation-specific NQR qualification mapped to NSQF Level 1.",
            "Relevant evidence can include an entry-level vocational qualification, recognised short-term training or employer competency evidence where the occupation permits it.",
            "Do not treat a generic certificate as universally required for Level 1; verify the occupation's NQR qualification and awarding body.",
        ],
    },
    2: {
        "title": "Elementary / Assistant",
        "knowledge": [
            "Fundamental knowledge of the work area and common work procedures.",
            "Understands basic operational concepts, terminology, tools and materials.",
            "Can relate simple instructions to routine work situations.",
        ],
        "technical_skills": [
            "Performs a limited range of finite, routine skills.",
            "Uses standard tools, equipment and procedures for familiar tasks.",
            "Carries out basic measurements, checks and simple operational activities.",
        ],
        "aptitude_employability": [
            "Can read and understand basic workplace information where required.",
            "Demonstrates basic communication, teamwork, safety and work discipline.",
            "Can follow structured instructions and identify an obvious deviation.",
        ],
        "learning_outcomes": [
            "Performs structured and routine tasks using known solutions.",
            "Identifies simple problems and seeks guidance for non-routine issues.",
            "Can adapt a known procedure within clearly defined limits.",
        ],
        "responsibility": [
            "Works as an assistant with limited responsibility.",
            "Works under supervision, although supervision may be less continuous than Level 1.",
            "Is responsible for the quality and safe completion of assigned routine work.",
        ],
        "typical_role": "Assistant",
        "entry_and_training": "The framework generally allows no formal education for Level 2, with basic literacy/readiness depending on the qualification; around 210–270 hours of short-term training is indicated, and some qualifications may value about one year of experience.",
        "certification_guidance": [
            "Search NQR for an occupation-specific Level 2 qualification.",
            "Useful evidence may include an NSQF-aligned Level 2 vocational qualification, recognised trade training or documented workplace competency.",
            "The exact awarding/certifying body depends on the sector and qualification.",
        ],
    },
    2.5: {
        "title": "Developing Skilled Worker",
        "knowledge": [
            "Has a broader range of knowledge than Level 2 within a defined occupational area.",
            "Understands standard procedures, terminology and common operating conditions.",
            "Can connect practical knowledge with routine work requirements.",
        ],
        "technical_skills": [
            "Applies a broader set of operational skills using standard procedures.",
            "Performs tasks with some discretion within established limits.",
            "Uses tools and equipment appropriately and performs routine quality checks.",
        ],
        "aptitude_employability": [
            "Demonstrates growing independence, teamwork and workplace communication.",
            "Can recognise routine deviations and seek or apply known solutions.",
            "Shows readiness to plan basic work activities.",
        ],
        "learning_outcomes": [
            "Performs a range of standard tasks rather than a single repetitive task.",
            "Identifies routine problems and applies known solutions.",
            "Can organise work within a defined sequence and time requirement.",
        ],
        "responsibility": [
            "Works with limited supervision.",
            "Takes responsibility for quality and timely delivery of assigned work.",
            "Can support team activities within a defined role.",
        ],
        "typical_role": "Developing Skilled Worker / Technician",
        "entry_and_training": "The framework associates Level 2.5 with routes such as Grade 9 or Grade 8 with continuous schooling, with short-term training broadly around 240–300 hours.",
        "certification_guidance": [
            "Verify an occupation-specific NQR Level 2.5 qualification where one exists.",
            "Use recognised vocational training and documented competency as supporting evidence rather than assuming a universal certificate.",
            "Confirm the awarding body and qualification-specific eligibility in NQR.",
        ],
    },
    3: {
        "title": "Skilled Worker / Technician",
        "knowledge": [
            "Has a range of knowledge of facts, principles, processes and general concepts in the occupational area.",
            "Understands standard procedures and how they relate to routine work outcomes.",
            "Can apply practical knowledge to familiar work situations.",
        ],
        "technical_skills": [
            "Uses a range of practical and technical skills for standard work.",
            "Operates tools and equipment and performs quality checks.",
            "Can plan and sequence routine work within established procedures.",
        ],
        "aptitude_employability": [
            "Demonstrates teamwork, communication and employment readiness.",
            "Can exercise limited discretion within standard procedures.",
            "Can identify problems and select known solutions.",
        ],
        "learning_outcomes": [
            "Performs skilled routine work with increasing independence.",
            "Handles standard variations and routine problems.",
            "Can organise tasks, resources and basic work priorities.",
        ],
        "responsibility": [
            "Works with limited supervision.",
            "Takes responsibility for quality and delivery of own work.",
            "May contribute as a skilled worker or technician within a team.",
        ],
        "typical_role": "Skilled Worker / Technician",
        "entry_and_training": "The framework generally associates Level 3 with Grade 10 or specified Grade 8 vocational routes, no experience normally required, and about 270–390 hours of short-term training.",
        "certification_guidance": [
            "Look for the relevant NQR Level 3 qualification for the occupation.",
            "Sector qualifications, ITI/trade credentials or other recognised vocational evidence may support the assessment when they map to the relevant occupation.",
            "Check the qualification's awarding/certifying body and eligibility rather than assuming a universal Level 3 certificate.",
        ],
    },
    3.5: {
        "title": "Advanced Skilled Worker / Technician",
        "knowledge": [
            "Has specialised knowledge within a defined occupational area.",
            "Understands procedures, operating conditions and quality requirements in greater depth.",
            "Can relate technical knowledge to more varied work situations.",
        ],
        "technical_skills": [
            "Applies proficient procedural and technical skills.",
            "Handles more complex or variable routine tasks.",
            "Can organise work and make limited technical decisions within defined boundaries.",
        ],
        "aptitude_employability": [
            "Demonstrates stronger communication, teamwork and employability skills.",
            "Can manage time and quality requirements.",
            "Shows readiness to support or guide other workers in familiar activities.",
        ],
        "learning_outcomes": [
            "Identifies and resolves a broader range of occupational problems.",
            "Adapts established procedures to work conditions within permitted limits.",
            "Can evaluate basic feasibility, quality and resource considerations.",
        ],
        "responsibility": [
            "Works with minimal supervision for defined technical activities.",
            "Can take responsibility for work quality and coordination of assigned activities.",
            "May function as an advanced technician or experienced skilled worker.",
        ],
        "typical_role": "Advanced Technician / Skilled Worker",
        "entry_and_training": "Typical entry routes include Grade 11, first year of a three-year diploma or specified vocational combinations; short-term training is broadly around 360–420 hours.",
        "certification_guidance": [
            "Verify an occupation-specific NQR Level 3.5 qualification if available.",
            "Use advanced trade/vocational training, diploma progression or documented occupational competence as supporting evidence.",
            "Certification remains qualification-specific and should be checked against NQR.",
        ],
    },
    4: {
        "title": "Senior Technician / Master Technician",
        "knowledge": [
            "Has specialised knowledge of facts, principles, processes and general concepts in an occupational area.",
            "Understands proficient procedural knowledge and more complex work requirements.",
            "Can consider time, quality, data and financial feasibility in work decisions.",
        ],
        "technical_skills": [
            "Uses advanced technical skills for complex and non-routine tasks.",
            "Performs fault diagnosis, planning, quality assurance and controlled technical activities.",
            "Can select appropriate methods, tools and resources for the task.",
        ],
        "aptitude_employability": [
            "Demonstrates leadership, communication and employment readiness.",
            "Can coordinate work and support others in achieving quality and safety requirements.",
            "Shows judgement when choosing among established technical approaches.",
        ],
        "learning_outcomes": [
            "Solves complex problems using specialised knowledge and established methods.",
            "Plans and manages work with limited supervision.",
            "Can evaluate work outcomes against technical, quality and resource constraints.",
        ],
        "responsibility": [
            "Works with minimal supervision.",
            "Takes individual and collective accountability for assigned work.",
            "Can function as a senior or master technician and may guide a work team.",
        ],
        "typical_role": "Senior Technician / Master Technician",
        "entry_and_training": "Typical routes include Grade 12, second year of a three-year diploma, or specified combinations of Grade 10 with NTC/NAC/CITS and related credentials; short-term training is broadly around 390–480 hours.",
        "certification_guidance": [
            "Search NQR for the occupation-specific Level 4 qualification before recommending certification.",
            "Relevant evidence may include ITI/NTC/NAC/CITS pathways, diplomas or other recognised sector qualifications when the target occupation accepts them.",
            "Do not claim that one certificate is mandatory for all Level 4 occupations; verify the NQR qualification and awarding body.",
        ],
    },
    4.5: {
        "title": "Advanced Technician / Emerging Professional",
        "knowledge": [
            "Has multidisciplinary or deeper specialised knowledge relevant to the occupation.",
            "Understands complex processes, interdependencies and work constraints.",
            "Can apply knowledge across related occupational situations.",
        ],
        "technical_skills": [
            "Performs complex technical work and applies advanced procedures.",
            "Uses data and technical information to support decisions.",
            "Can contribute to project planning, process improvement and quality management.",
        ],
        "aptitude_employability": [
            "Demonstrates stronger leadership, communication and entrepreneurial mindset.",
            "Can coordinate people, time, quality and resources.",
            "Shows judgement in complex work situations.",
        ],
        "learning_outcomes": [
            "Solves complex problems using specialised knowledge and evidence.",
            "Can manage components of projects or operational activities.",
            "Evaluates alternatives and their technical or operational consequences.",
        ],
        "responsibility": [
            "Can operate with substantial autonomy within a defined area.",
            "May supervise technical work or manage a small independent unit.",
            "Takes responsibility for improving outputs and processes.",
        ],
        "typical_role": "Advanced Technician / Junior Technical Professional",
        "entry_and_training": "Typical routes include first year of an undergraduate programme or a completed three-year diploma/diploma after Grade 12; training is broadly around 450–510 hours.",
        "certification_guidance": [
            "Use the occupation-specific NQR Level 4.5 qualification as the certification reference.",
            "Undergraduate progression, diploma qualifications and recognised sector credentials can provide supporting evidence where applicable.",
            "Verify exact qualification eligibility and awarding body in NQR.",
        ],
    },
    5: {
        "title": "Technical Supervisor / Junior Deputy Manager",
        "knowledge": [
            "Has multidisciplinary knowledge or deep specialised knowledge in a field.",
            "Understands complex processes, systems and relationships across work activities.",
            "Can apply knowledge to variable and non-routine occupational situations.",
        ],
        "technical_skills": [
            "Uses advanced technical skills to solve complex problems.",
            "Applies project management, data analysis and process/quality controls.",
            "Can plan, coordinate and optimise work, resources and outputs.",
        ],
        "aptitude_employability": [
            "Demonstrates entrepreneurial mindset, leadership and strong employability skills.",
            "Can communicate decisions and coordinate teams.",
            "Uses judgement to select appropriate approaches under changing conditions.",
        ],
        "learning_outcomes": [
            "Analyses complex problems and develops practical solutions.",
            "Can manage projects or an independent operational unit.",
            "Improves processes, productivity, quality or resource utilisation.",
        ],
        "responsibility": [
            "Operates with significant autonomy within an area of responsibility.",
            "Takes accountability for team or unit performance and delivery.",
            "May function as a technical supervisor, junior manager or deputy manager.",
        ],
        "typical_role": "Technical Supervisor / Junior Deputy Manager",
        "entry_and_training": "Typical routes include completion or pursuit of the second year of an undergraduate programme or second year of a diploma after Grade 12; short-term training is broadly around 480–570 hours, with internship/project options.",
        "certification_guidance": [
            "Search NQR for the specific occupation's Level 5 qualification.",
            "Relevant evidence can include advanced sector qualifications, diplomas, undergraduate progression or recognised professional/technical credentials accepted by the target qualification.",
            "The NQR qualification's awarding/certifying body and eligibility should be used as the authoritative certification check.",
        ],
    },
    5.5: {
        "title": "Professional / Senior Technical Specialist",
        "knowledge": [
            "Has advanced multidisciplinary or specialised knowledge.",
            "Understands emerging developments and complex systems in the occupational area.",
            "Can integrate knowledge from related domains.",
        ],
        "technical_skills": [
            "Handles complex and variable technical or professional tasks.",
            "Uses advanced analysis, project management and improvement methods.",
            "Can design and implement solutions with measurable outcomes.",
        ],
        "aptitude_employability": [
            "Demonstrates leadership, professional judgement and entrepreneurial capability.",
            "Can manage stakeholders, teams and competing priorities.",
            "Uses evidence and risk considerations in decisions.",
        ],
        "learning_outcomes": [
            "Analyses complex situations and develops evidence-based solutions.",
            "Leads improvement initiatives and manages projects.",
            "Can evaluate performance using KPIs and operational evidence.",
        ],
        "responsibility": [
            "Takes substantial responsibility for an independent unit, project or specialist area.",
            "Can lead teams and coordinate cross-functional activities.",
            "Is accountable for outcomes and continuous improvement.",
        ],
        "typical_role": "Professional / Senior Technical Specialist",
        "entry_and_training": "The framework places Level 5.5 around undergraduate degree progression, with short-term training broadly around 540–600 hours and internship/project options.",
        "certification_guidance": [
            "Verify the occupation-specific NQR Level 5.5 qualification.",
            "Professional, technical and undergraduate credentials may support the evidence where the target qualification recognises them.",
            "Do not infer a universal certificate from the level alone.",
        ],
    },
    6: {
        "title": "Senior Manager / Senior Technical Manager",
        "knowledge": [
            "Has advanced knowledge of a field, including emerging developments.",
            "Understands complex and variable environments and their wider organisational implications.",
            "Can integrate specialist knowledge across functions.",
        ],
        "technical_skills": [
            "Uses advanced analytical, leadership and management skills.",
            "Applies risk-based and evidence-based decision making.",
            "Leads process improvement, resource planning and performance management.",
        ],
        "aptitude_employability": [
            "Demonstrates leadership, management and professional judgement.",
            "Can set and monitor KPIs and manage stakeholders.",
            "Shows capacity for innovation and organisational improvement.",
        ],
        "learning_outcomes": [
            "Solves complex problems in changing environments.",
            "Leads independent business units, major projects or specialist functions.",
            "Evaluates performance and implements strategic or operational improvements.",
        ],
        "responsibility": [
            "Has broad autonomy and accountability for a unit, project or function.",
            "Takes responsibility for people, resources, quality and outcomes.",
            "May function as a manager or senior manager.",
        ],
        "typical_role": "Senior Manager / Senior Technical Manager",
        "entry_and_training": "Typical routes include first year of postgraduate study after a three-year undergraduate degree, a one-year postgraduate diploma, or completed/pursuing four-year undergraduate study; training is broadly around 570–660 hours.",
        "certification_guidance": [
            "Use the occupation-specific NQR Level 6 qualification as the certification reference.",
            "Postgraduate, professional and advanced sector qualifications can be supporting evidence when accepted by the target qualification.",
            "Verify the qualification-specific awarding body and eligibility.",
        ],
    },
    6.5: {
        "title": "Advanced Professional / Specialist Leader",
        "knowledge": [
            "Has advanced and increasingly specialised knowledge of a field.",
            "Understands emerging developments, complex systems and cross-domain relationships.",
            "Can critically evaluate established knowledge and approaches.",
        ],
        "technical_skills": [
            "Uses highly developed analytical, professional and leadership skills.",
            "Designs solutions for complex and changing environments.",
            "Can lead multidisciplinary initiatives and improvement programmes.",
        ],
        "aptitude_employability": [
            "Demonstrates advanced leadership, professional judgement and innovation.",
            "Can manage significant uncertainty and competing stakeholder needs.",
            "Shows readiness for strategic and research-oriented work.",
        ],
        "learning_outcomes": [
            "Evaluates complex problems and develops evidence-based solutions.",
            "Leads change and improvement across teams or functions.",
            "Can integrate specialist knowledge to create new or improved approaches.",
        ],
        "responsibility": [
            "Has substantial autonomy and accountability.",
            "Leads major projects, specialist functions or multidisciplinary teams.",
            "Is accountable for strategic outcomes within a defined area.",
        ],
        "typical_role": "Advanced Professional / Specialist Leader",
        "entry_and_training": "Typical routes include postgraduate or doctoral progression; short-term training is broadly around 630–690 hours in the descriptor framework.",
        "certification_guidance": [
            "Verify an occupation-specific NQR Level 6.5 qualification if available.",
            "Advanced professional, postgraduate or specialist credentials may support the evidence.",
            "Certification remains occupation-specific rather than universal by level.",
        ],
    },
    7: {
        "title": "Director / CEO / Advanced Specialist",
        "knowledge": [
            "Has advanced critical knowledge of a field and its interfaces with related domains.",
            "Understands highly complex systems, emerging developments and strategic implications.",
            "Can critically evaluate and extend professional knowledge.",
        ],
        "technical_skills": [
            "Uses highly specialised and transdisciplinary skills.",
            "Develops innovative solutions to complex and unpredictable problems.",
            "Applies change management, strategic planning and advanced leadership.",
        ],
        "aptitude_employability": [
            "Demonstrates strategic leadership, innovation and entrepreneurial capability.",
            "Makes high-level decisions under uncertainty.",
            "Can lead transformation and communicate strategic direction.",
        ],
        "learning_outcomes": [
            "Creates original approaches or solutions for complex problems.",
            "Leads strategic initiatives and organisational change.",
            "Integrates evidence, risk, technology and stakeholder considerations.",
        ],
        "responsibility": [
            "Has broad strategic autonomy and accountability.",
            "Leads major functions, organisations, programmes or advanced specialist practice.",
            "May operate at director, CEO-equivalent or advanced specialist level.",
        ],
        "typical_role": "Director / CEO / Advanced Specialist",
        "entry_and_training": "Typical routes include postgraduate engineering/professional study or doctoral progression; short-term training is broadly around 660–750 hours.",
        "certification_guidance": [
            "Verify the target occupation's NQR Level 7 qualification.",
            "Postgraduate, advanced professional and specialist credentials can be supporting evidence where recognised.",
            "Do not equate a job title such as CEO with NSQF Level 7 without competency evidence.",
        ],
    },
    8: {
        "title": "Thought Leader / Board-Level / Transformational Expert",
        "knowledge": [
            "Demonstrates mastery and comprehensive knowledge of a field and its boundaries.",
            "Understands the most advanced developments and complex interdisciplinary systems.",
            "Can generate and critically evaluate new knowledge.",
        ],
        "technical_skills": [
            "Uses the most advanced and specialised skills to solve complex problems.",
            "Develops evidence-based, original and transformational solutions.",
            "Leads large-scale research, innovation or organisational transformation.",
        ],
        "aptitude_employability": [
            "Demonstrates transformational leadership and strategic vision.",
            "Can shape direction across organisations, sectors or knowledge domains.",
            "Shows high-level innovation, influence and responsible decision making.",
        ],
        "learning_outcomes": [
            "Creates new knowledge, methods or solutions for complex and unresolved problems.",
            "Leads large transformation programmes and strategic change.",
            "Shapes long-term organisational or professional direction.",
        ],
        "responsibility": [
            "Has the highest level of autonomy and accountability.",
            "Can act as a thought leader, board-level expert, CMD/chairperson or equivalent.",
            "Takes responsibility for strategic vision, organisational growth and transformation.",
        ],
        "typical_role": "Thought Leader / Board-Level Expert / Transformational Leader",
        "entry_and_training": "The framework associates Level 8 with doctoral-level routes and very extensive experience routes; training is 750+ hours in the descriptor table, with a PhD in a relevant field listed as one route without requiring prior experience.",
        "certification_guidance": [
            "Verify an occupation-specific NQR Level 8 qualification where one exists.",
            "A relevant PhD and advanced professional/sector credentials can be important evidence, but the level is based on demonstrated learning outcomes, not the degree title alone.",
            "Confirm the specific qualification, awarding body and eligibility in NQR.",
        ],
    },
}


NSQF_LEVEL_OPTIONS = [1, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 8]

# The current LLM integration intentionally receives only Levels 1–5.
# Once a proper NQR qualification/descriptor API is available, this boundary
# can be raised without changing the stored descriptor data.
PROMPT_LEVEL_MAX = 5


def prompt_level_descriptors() -> dict:
    return {
        level: NSQF_LEVEL_DESCRIPTORS[level]
        for level in range(1, PROMPT_LEVEL_MAX + 1)
    }

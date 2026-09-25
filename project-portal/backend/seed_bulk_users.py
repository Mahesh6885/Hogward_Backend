"""
seed_bulk_users.py — Adds 40 test users to the database.

Idempotent: skips users that already exist (by username).
Also writes `test_credentials.txt` with all usernames and passwords.

Usage:
    cd project-portal/backend
    python seed_bulk_users.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.security import hash_password
from app.database.database import SessionLocal, engine
from app.database.base import Base
from app.models.user import User, UserRole, UserStatus
from app.models.domain import Domain, DomainName
import app.models  # noqa: F401


TEST_USERS = [
    # AI domain (14)
    ("Team NeuralNexus",    "team_neuralnexus",    "neuralnexus@test.com",    "AI",            "Team NeuralNexus",    "Arjun Sharma",    "Priya Nair",      "Rohit Das",     "Sneha Pillai",  "IIT Bombay",         "Computer Science",    "2025-2026"),
    ("Team DeepMind Delta", "team_deepmind_delta", "deepminddelta@test.com",  "AI",            "Team DeepMind Delta", "Kiran Mehta",     "Anjali Verma",    "Suresh Reddy",  "Divya Rajan",   "IIT Delhi",          "AI and ML",           "2025-2026"),
    ("Team AlphaWave",      "team_alphawave",      "alphawave@test.com",      "AI",            "Team AlphaWave",      "Vikram Singh",    "Pooja Mishra",    "Ankit Gupta",   "Riya Kapoor",   "NIT Trichy",         "Data Science",        "2025-2026"),
    ("Team VisionCore",     "team_visioncore",     "visioncore@test.com",     "AI",            "Team VisionCore",     "Rahul Patel",     "Meena Iyer",      "Sanjay Kumar",  "Tara Bose",     "VIT Vellore",        "Computer Vision",     "2025-2026"),
    ("Team SynthIQ",        "team_synthiq",        "synthiq@test.com",        "AI",            "Team SynthIQ",        "Aditya Joshi",    "Kavitha Rao",     "Nikhil Menon",  None,            "BITS Pilani",        "Artificial Intel.",   "2025-2026"),
    ("Team LogicForge",     "team_logicforge",     "logicforge@test.com",     "AI",            "Team LogicForge",     "Harish Nambiar",  "Shruti Tiwari",   "Pranav Yadav",  "Lakshmi Pillai","SRM University",     "Machine Learning",    "2025-2026"),
    ("Team EdgeBrain",      "team_edgebrain",      "edgebrain@test.com",      "AI",            "Team EdgeBrain",      "Vinay Choudhary", "Deepa Krishnan",  "Manoj Patil",   "Nisha Sharma",  "Manipal University", "Computer Science",    "2025-2026"),
    ("Team OmegaAI",        "team_omegaai",        "omegaai@test.com",        "AI",            "Team OmegaAI",        "Sandeep Ravi",    "Geeta Nair",      "Tarun Jain",    "Pallavi Mehta", "Anna University",    "AI and Robotics",     "2025-2026"),
    ("Team QuantumLeap",    "team_quantumleap",    "quantumleap@test.com",    "AI",            "Team QuantumLeap",    "Rajesh Kumar",    "Swathi Reddy",    "Aryan Bose",    None,            "Jadavpur University","Deep Learning",       "2025-2026"),
    ("Team NovaMind",       "team_novamind",       "novamind@test.com",       "AI",            "Team NovaMind",       "Varun Sharma",    "Asha Pillai",     "Ravi Teja",     "Shalini Gupta", "Amrita University",  "Neural Networks",     "2025-2026"),
    ("Team PulseCog",       "team_pulsecog",       "pulsecog@test.com",       "AI",            "Team PulseCog",       "Kiran Raj",       "Bhavna Iyer",     "Gaurav Singh",  "Nandita Das",   "PSG College",        "AI Engineering",      "2025-2026"),
    ("Team ZeroGravAI",     "team_zerogravai",     "zerogravai@test.com",     "AI",            "Team ZeroGravAI",     "Mohit Verma",     "Chitra Menon",    "Lokesh Reddy",  "Ananya Rao",    "CEG Chennai",        "Computer Science",    "2025-2026"),
    ("Team FusionNet",      "team_fusionnet",      "fusionnet@test.com",      "AI",            "Team FusionNet",      "Suman Ghosh",     "Rekha Krishnan",  "Arun Pandey",   None,            "IIIT Hyderabad",     "ML and Data Science", "2025-2026"),
    ("Team NexusByte",      "team_nexusbyte",      "nexusbyte@test.com",      "AI",            "Team NexusByte",      "Dinesh Patel",    "Vandana Sharma",  "Sunil Mishra",  "Farah Khan",    "Thapar University",  "AI Research",         "2025-2026"),
    # Cybersecurity domain (13)
    ("Team CipherX",        "team_cipherx",        "cipherx@test.com",        "CYBERSECURITY", "Team CipherX",        "Akash Dubey",     "Nandini Bose",    "Vasudev Rao",   "Preethi Nair",  "IIT Madras",         "Cybersecurity",       "2025-2026"),
    ("Team GhostNet",       "team_ghostnet",       "ghostnet@test.com",       "CYBERSECURITY", "Team GhostNet",       "Naveen Kumar",    "Soumya Das",      "Harshit Joshi", None,            "IIT Roorkee",        "Network Security",    "2025-2026"),
    ("Team PhantomByte",    "team_phantombyte",    "phantombyte@test.com",    "CYBERSECURITY", "Team PhantomByte",    "Vivek Nair",      "Smitha Pillai",   "Deven Shah",    "Ritu Gupta",    "NIT Surathkal",      "Ethical Hacking",     "2025-2026"),
    ("Team IronShield",     "team_ironshield",     "ironshield@test.com",     "CYBERSECURITY", "Team IronShield",     "Sriram Iyengar",  "Madhavi Iyer",    "Rohit Sinha",   "Kavya Menon",   "IIIT Bangalore",     "Cryptography",        "2025-2026"),
    ("Team DarkVector",     "team_darkvector",     "darkvector@test.com",     "CYBERSECURITY", "Team DarkVector",     "Suresh Babu",     "Gayathri Raj",    "Kiran Desai",   None,            "Amity University",   "Forensics",           "2025-2026"),
    ("Team ZeroDay",        "team_zeroday",        "zeroday@test.com",        "CYBERSECURITY", "Team ZeroDay",        "Amar Srivastava", "Sunita Pandey",   "Yash Kapoor",   "Tanya Singh",   "Symbiosis Institute","Penetration Testing", "2025-2026"),
    ("Team SteelGuard",     "team_steelguard",     "steelguard@test.com",     "CYBERSECURITY", "Team SteelGuard",     "Mahesh Iyer",     "Deepika Raman",   "Souvik Das",    "Arpita Roy",    "Manipal University", "Network Defence",     "2025-2026"),
    ("Team NullByte",       "team_nullbyte",       "nullbyte@test.com",       "CYBERSECURITY", "Team NullByte",       "Rajan Pillai",    "Anitha Kumar",    "Dev Sharma",    None,            "SRM University",     "Cybersecurity",       "2025-2026"),
    ("Team ByteForce",      "team_byteforce",      "byteforce@test.com",      "CYBERSECURITY", "Team ByteForce",      "Praveen Reddy",   "Lalitha Menon",   "Shankar Rao",   "Isha Malhotra", "SASTRA University",  "Security Engineering","2025-2026"),
    ("Team HexHunter",      "team_hexhunter",      "hexhunter@test.com",      "CYBERSECURITY", "Team HexHunter",      "Ashwin Kumar",    "Yamini Naidu",    "Siddharth Roy", "Neha Agarwal",  "Karunya University", "Ethical Hacking",     "2025-2026"),
    ("Team FortressX",      "team_fortressx",      "fortressx@test.com",      "CYBERSECURITY", "Team FortressX",      "Balaji Krishnan", "Padma Suresh",    "Nilesh Patil",  None,            "CIT Coimbatore",     "Cloud Security",      "2025-2026"),
    ("Team RedTeam9",       "team_redteam9",       "redteam9@test.com",       "CYBERSECURITY", "Team RedTeam9",       "Surya Prakash",   "Jaya Lakshmi",    "Aditya Rout",   "Pooja Sharma",  "Chandigarh Univ.",   "Red Teaming",         "2025-2026"),
    ("Team VigilanceOps",   "team_vigilanceops",   "vigilanceops@test.com",   "CYBERSECURITY", "Team VigilanceOps",   "Ramesh Babu",     "Kavitha Srinivas","Girish Nair",   "Anjali Rathi",  "PESIT Bangalore",    "SOC Operations",      "2025-2026"),
    # Open Innovation domain (13)
    ("Team Ignite360",      "team_ignite360",      "ignite360@test.com",      "OPEN_INNOVATION","Team Ignite360",     "Aarav Shah",      "Ishaan Mehta",    "Disha Kapoor",  "Kriti Nair",    "DSCE Bangalore",     "Innovation Design",   "2025-2026"),
    ("Team VaultVision",    "team_vaultvision",    "vaultvision@test.com",    "OPEN_INNOVATION","Team VaultVision",   "Prakash Iyer",    "Sindhu Rajan",    "Alok Mishra",   None,            "GEC Thrissur",       "Product Design",      "2025-2026"),
    ("Team BlueSparks",     "team_bluesparks",     "bluesparks@test.com",     "OPEN_INNOVATION","Team BlueSparks",    "Tejesh Kumar",    "Chaitra Reddy",   "Nitin Bhat",    "Ranjana Patel", "NITK Surathkal",     "Embedded Systems",    "2025-2026"),
    ("Team Tectonic",       "team_tectonic",       "tectonic@test.com",       "OPEN_INNOVATION","Team Tectonic",      "Gopal Shankar",   "Preethi Menon",   "Suhas Rao",     "Bhoomika Jain", "BIT Mesra",          "Emerging Tech",       "2025-2026"),
    ("Team SolarFlux",      "team_solarflux",      "solarflux@test.com",      "OPEN_INNOVATION","Team SolarFlux",     "Aryan Verma",     "Roshni Pillai",   "Tushar Sinha",  None,            "DAIICT Gandhinagar", "Green Technology",    "2025-2026"),
    ("Team PixelPulse",     "team_pixelpulse",     "pixelpulse@test.com",     "OPEN_INNOVATION","Team PixelPulse",    "Mithun Raj",      "Lakshanya Iyer",  "Yash Dubey",    "Swathi Pillai", "SIT Tumkur",         "UX and Design",       "2025-2026"),
    ("Team StormCell",      "team_stormcell",      "stormcell@test.com",      "OPEN_INNOVATION","Team StormCell",     "Deepak Sharma",   "Archana Reddy",   "Jayesh Patel",  "Shreya Gupta",  "RIT Bangalore",      "IoT Systems",         "2025-2026"),
    ("Team EchoLabs",       "team_echolabs",       "echolabs@test.com",       "OPEN_INNOVATION","Team EchoLabs",      "Santhosh Kumar",  "Vidya Nair",      "Prashant Roy",  None,            "JSSATE Bangalore",   "Product Development", "2025-2026"),
    ("Team TitanX",         "team_titanx",         "titanx@test.com",         "OPEN_INNOVATION","Team TitanX",        "Raghavendra Rao", "Uma Shankar",     "Kiran Pillai",  "Divya Sharma",  "MVJ College",        "Robotics",            "2025-2026"),
    ("Team AuraFlow",       "team_auraflow",       "auraflow@test.com",       "OPEN_INNOVATION","Team AuraFlow",      "Shiva Prasad",    "Nalini Krishnan", "Bhuvan Raj",    "Parvathy Iyer", "RNSIT Bangalore",    "AR VR Technology",    "2025-2026"),
    ("Team NovaSpark",      "team_novaspark",      "novaspark@test.com",      "OPEN_INNOVATION","Team NovaSpark",     "Abhishek Jain",   "Kavya Pillai",    "Santosh Das",   None,            "BMS College",        "Smart Systems",       "2025-2026"),
    ("Team CodeBridge",     "team_codebridge",     "codebridge@test.com",     "OPEN_INNOVATION","Team CodeBridge",    "Venkatesh Rao",   "Sridevi Menon",   "Mohan Lal",     "Geeta Singh",   "Nitte University",   "Software Innovation", "2025-2026"),
    ("Team WarpDrive",      "team_warpdrive",      "warpdrive@test.com",      "OPEN_INNOVATION","Team WarpDrive",     "Jayant Kumar",    "Kamala Nair",     "Srihari Bhat",  "Anushka Rao",   "Presidency College", "Future Tech",         "2025-2026"),
]


def make_password(username):
    suffix = username.replace('team_', '').capitalize()
    return f'Pass@{suffix}2025'


def main():
    print('\nStarting bulk user seed (40 users)...')
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    credentials = []
    created = 0
    skipped = 0
    try:
        domain_map = {}
        for dn in [DomainName.AI, DomainName.CYBERSECURITY, DomainName.OPEN_INNOVATION]:
            domain = db.query(Domain).filter(Domain.name == dn.value).first()
            if domain:
                domain_map[dn.value] = domain
            else:
                print(f'  [WARN] Domain {dn.value} not found - run seed.py first!')

        for (name, username, email, dname, team_name, leader, m1, m2, m3, college, dept, yr) in TEST_USERS:
            password = make_password(username)
            existing = db.query(User).filter(User.username == username).first()
            if existing:
                print(f'  - Skipped (exists): {username}')
                skipped += 1
                credentials.append((username, password, 'SKIPPED - already exists'))
                continue
            domain = domain_map.get(dname)
            user = User(
                name=name, username=username, email=email,
                password_hash=hash_password(password),
                role=UserRole.USER, status=UserStatus.ACTIVE,
                domain_id=domain.id if domain else None,
                team_name=team_name, team_leader=leader,
                member_one=m1, member_two=m2, member_three=m3,
                college_name=college, organization=college,
                department=dept,
            )
            db.add(user)
            db.flush()
            print(f'  [OK] Created: {username} ({dname})')
            created += 1
            credentials.append((username, password, dname))

        db.commit()
        print(f'\n[SUCCESS] Done! Created={created}, Skipped={skipped}\n')
    except Exception as e:
        db.rollback()
        print(f'\n[ERROR] {e}')
        raise
    finally:
        db.close()

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_credentials.txt')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('=' * 70 + '\n')
        f.write('  HOGWARD PROJECT PORTAL - TEST USER CREDENTIALS\n')
        f.write('=' * 70 + '\n\n')
        f.write(f'{"USERNAME":<30} {"PASSWORD":<25} {"DOMAIN"}\n')
        f.write('-' * 70 + '\n')
        for uname, pwd, domain in credentials:
            f.write(f'{uname:<30} {pwd:<25} {domain}\n')
        f.write('\n' + '=' * 70 + '\n')
        f.write('  NOTE: All users have role=USER and status=ACTIVE\n')
        f.write('  Admin credentials are in your .env file\n')
        f.write('=' * 70 + '\n')
    print(f'Credentials written to: {out_path}\n')


if __name__ == '__main__':
    main()

import json
import logging
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.orm import sessionmaker

# Configuration de la journalisation
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation de l'application Flask
app = Flask(__name__)

# Configuration de la base de données SQLite
DATABASE_URL = "sqlite:///quiz.db"
engine = create_engine(DATABASE_URL, echo=True)
metadata = MetaData()

# Définir la table des quiz
quiz_table = Table(
    'quiz', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('title', String, nullable=False),
    Column('questions', String, nullable=False)  # Utilisation de String pour simplifier
)

# Créer la table si elle n'existe pas
metadata.create_all(engine)

# Créer une session
Session = sessionmaker(bind=engine)
session = Session()

# Route d'accueil
@app.route('/', methods=['GET'])
def home():
    return '''<h1>Welcome, les amis 🤪</h1>
<h2>Venez défier vos connaissances avec nos quiz personnalisés ! 🧠💥</h2>
<p>Prêts à tester vos méninges et devenir un(e) expert(e) des quiz ? Créez et récupérez vos quiz personnalisés ici, et surtout, ne prenez pas tout trop au sérieux… sauf vos résultats ! 😜</p>
<p>Cette API a été réalisée avec amour par William et Keth. Profitez-en bien ! 😉</p>'''

# Route pour créer un quiz
@app.route('/api/quiz', methods=['POST'])
def create_quiz():
    data = request.json
    if not data or "title" not in data or "questions" not in data:
        return {"error": "Le titre et les questions sont obligatoires."}, 400

    new_quiz = {
        "title": data["title"],
        "questions": json.dumps(data["questions"])  # Convertir la liste en chaîne de caractères
    }

    try:
        conn = engine.connect()
        trans = conn.begin()
        logger.info("Connexion à la base de données établie.")
        ins = quiz_table.insert().values(new_quiz)
        result = conn.execute(ins)
        trans.commit()
        conn.close()
        logger.info("Quiz créé avec succès.")
        return {"message": "Quiz créé avec succès.", "quiz_id": result.inserted_primary_key[0]}, 201
    except Exception as e:
        logger.error(f"Erreur lors de la création du quiz : {e}")
        trans.rollback()
        conn.close()
        return {"error": "Erreur lors de la création du quiz."}, 500

# Route pour lister tous les quiz
@app.route('/api/quiz', methods=['GET'])
def list_quizzes():
    try:
        conn = engine.connect()
        logger.info("Connexion à la base de données établie pour la récupération des quiz.")
        sel = quiz_table.select()
        result = conn.execute(sel)
        quizzes = []
        for row in result:
            quiz = {
                "id": row[0],  # Utiliser l'indice numérique
                "title": row[1],  # Utiliser l'indice numérique
                "questions": json.loads(row[2])  # Convertir la chaîne de caractères en liste
            }
            quizzes.append(quiz)
        conn.close()
        return jsonify(quizzes)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des quiz : {e}")
        return {"error": "Erreur lors de la récupération des quiz."}, 500



# Route pour obtenir un quiz par ID
@app.route('/api/quiz/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    try:
        conn = engine.connect()
        logger.info(f"Connexion à la base de données établie pour la récupération du quiz avec ID {quiz_id}.")
        sel = quiz_table.select().where(quiz_table.c.id == quiz_id)
        result = conn.execute(sel).fetchone()
        conn.close()
        if result:
            quiz = {
                "id": result[0],  # Utiliser l'indice numérique
                "title": result[1],  # Utiliser l'indice numérique
                "questions": json.loads(result[2])  # Convertir la chaîne de caractères en liste
            }
            return jsonify(quiz)
        else:
            return {"error": "Quiz non trouvé."}, 404
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du quiz : {e}")
        return {"error": "Erreur lors de la récupération du quiz."}, 500



# Route pour jouer à un quiz
# Route pour jouer à un quiz
@app.route('/api/quiz/play/<int:quiz_id>', methods=['POST'])
def play_quiz(quiz_id):
    try:
        conn = engine.connect()
        logger.info(f"Connexion à la base de données établie pour jouer au quiz avec ID {quiz_id}.")
        sel = quiz_table.select().where(quiz_table.c.id == quiz_id)
        result = conn.execute(sel).fetchone()
        conn.close()
        if not result:
            return {"error": "Quiz non trouvé."}, 404

        data = request.json
        if not data or "answers" not in data:
            return {"error": "Les réponses sont obligatoires."}, 400

        user_answers = data["answers"]
        correct_answers = [q.get("answer") for q in json.loads(result[2])]  # Utiliser l'indice numérique

        # Calculer le score
        score = sum(
            1 for user_answer, correct_answer in zip(user_answers, correct_answers) if user_answer == correct_answer)
        total_questions = len(correct_answers)

        return {
            "message": "Quiz terminé.",
            "score": score,
            "total": total_questions
        }
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du quiz : {e}")
        return {"error": "Erreur lors de la lecture du quiz."}, 500
    
# Route pour supprimer un quiz
# Route pour supprimer un quiz
@app.route('/api/quiz/<int:quiz_id>', methods=['DELETE'])
def delete_quiz(quiz_id):
    try:
        conn = engine.connect()
        trans = conn.begin()
        logger.info(f"Connexion à la base de données établie pour supprimer le quiz avec ID {quiz_id}.")
        sel = quiz_table.select().where(quiz_table.c.id == quiz_id)
        result = conn.execute(sel).fetchone()
        if not result:
            conn.close()
            return {"error": "Quiz non trouvé."}, 404

        del_stmt = quiz_table.delete().where(quiz_table.c.id == quiz_id)
        conn.execute(del_stmt)
        trans.commit()
        conn.close()
        logger.info("Quiz supprimé avec succès.")
        return {"message": "Quiz supprimé avec succès."}, 200
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du quiz : {e}")
        trans.rollback()
        conn.close()
        return {"error": "Erreur lors de la suppression du quiz."}, 500


# Route pour mettre à jour un quiz
# Route pour mettre à jour un quiz
@app.route('/api/quiz/<int:quiz_id>', methods=['PUT'])
def update_quiz(quiz_id):
    data = request.json
    if not data or "title" not in data or "questions" not in data:
        return {"error": "Le titre et les questions sont obligatoires."}, 400

    try:
        conn = engine.connect()
        trans = conn.begin()
        logger.info(f"Connexion à la base de données établie pour mettre à jour le quiz avec ID {quiz_id}.")
        sel = quiz_table.select().where(quiz_table.c.id == quiz_id)
        result = conn.execute(sel).fetchone()
        if not result:
            conn.close()
            return {"error": "Quiz non trouvé."}, 404

        update_stmt = quiz_table.update().where(quiz_table.c.id == quiz_id).values(
            title=data["title"],
            questions=json.dumps(data["questions"])  # Convertir la liste en chaîne de caractères
        )
        conn.execute(update_stmt)
        trans.commit()
        conn.close()
        logger.info("Quiz mis à jour avec succès.")
        return {"message": "Quiz mis à jour avec succès."}, 200
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du quiz : {e}")
        trans.rollback()
        conn.close()
        return {"error": "Erreur lors de la mise à jour du quiz."}, 500



# Exécution de l'application
if __name__ == "__main__":
    app.run(debug=True)

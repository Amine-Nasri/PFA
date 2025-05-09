require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const session = require('express-session');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Configuration de MongoDB
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/violenceDetection', {
    useNewUrlParser: true,
    useUnifiedTopology: true
});

const db = mongoose.connection;
db.on('error', console.error.bind(console, 'Erreur de connexion à MongoDB:'));
db.once('open', () => {
    console.log('Connecté à MongoDB');
});

// Modèle utilisateur
const UserSchema = new mongoose.Schema({
    fullName: { type: String, required: true },
    email: { type: String, required: true, unique: true },
    password: { type: String, required: true },
    createdAt: { type: Date, default: Date.now }
});

const User = mongoose.model('User', UserSchema);

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));
app.use(session({
    secret: process.env.SESSION_SECRET || 'votre_secret_session',
    resave: false,
    saveUninitialized: false,
    cookie: { secure: false, maxAge: 24 * 60 * 60 * 1000 } // 24 heures
}));

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/dashboard', (req, res) => {
    if (!req.session.user) {
        return res.redirect('/');
    }
    res.sendFile(path.join(__dirname, 'public', 'dashboard.html'));
});

// Inscription
app.post('/register', async (req, res) => {
    try {
        const { fullName, email, password, confirmPassword } = req.body;

        // Validation
        if (password !== confirmPassword) {
            return res.status(400).json({ error: 'Les mots de passe ne correspondent pas' });
        }

        // Vérifier si l'utilisateur existe déjà
        const existingUser = await User.findOne({ email });
        if (existingUser) {
            return res.status(400).json({ error: 'Cet email est déjà utilisé' });
        }

        // Hacher le mot de passe
        const hashedPassword = await bcrypt.hash(password, 10);

        // Créer un nouvel utilisateur
        const newUser = new User({
            fullName,
            email,
            password: hashedPassword
        });

        await newUser.save();

        // Créer la session
        req.session.user = {
            id: newUser._id,
            email: newUser.email,
            fullName: newUser.fullName
        };

        res.json({ success: true, redirect: '/dashboard' });

    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Erreur lors de l\'inscription' });
    }
});

// Connexion
app.post('/login', async (req, res) => {
    try {
        const { email, password } = req.body;

        // Trouver l'utilisateur
        const user = await User.findOne({ email });
        if (!user) {
            return res.status(400).json({ error: 'Email ou mot de passe incorrect' });
        }

        // Vérifier le mot de passe
        const isMatch = await bcrypt.compare(password, user.password);
        if (!isMatch) {
            return res.status(400).json({ error: 'Email ou mot de passe incorrect' });
        }

        // Créer la session
        req.session.user = {
            id: user._id,
            email: user.email,
            fullName: user.fullName
        };

        res.json({ success: true, redirect: '/dashboard' });

    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Erreur lors de la connexion' });
    }
});

// Déconnexion
app.get('/logout', (req, res) => {
    req.session.destroy(err => {
        if (err) {
            return res.status(500).json({ error: 'Erreur lors de la déconnexion' });
        }
        res.clearCookie('connect.sid');
        res.redirect('/');
    });
});

// API pour l'analyse de violence
app.post('/analyze', async (req, res) => {
    try {
        if (!req.session.user) {
            return res.status(401).json({ error: 'Non autorisé' });
        }

        const { video_url } = req.body;
        
        // Ici vous intégrerez votre logique d'analyse de violence
        // Pour l'exemple, nous retournons des données simulées
        
        const analysisResult = {
            status: "completed",
            average_score: Math.random(),
            frames_analyzed: Math.floor(Math.random() * 100) + 50,
            graph_url: "/graphs/sample.png" // Chemin vers un graphique exemple
        };

        res.json(analysisResult);

    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Erreur lors de l\'analyse' });
    }
});

// Démarrer le serveur
app.listen(PORT, () => {
    console.log(`Serveur démarré sur http://localhost:${PORT}`);
});
const express = require('express');
const path = require('path');
const app = express();
const port = 3000;

// Serve static files from 'public' directory
app.use(express.static('public'));

// Routes for specific pages
app.get('/game', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'game.html'));
});

app.get('/security', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'security.html'));
});

app.get('/prize', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'prize.html'));
});

// Download endpoint
app.get('/download-file/:filename', (req, res) => {
    const filename = req.params.filename;
    // Basic security check to prevent directory traversal
    if (filename.includes('..') || filename.includes('/')) {
        return res.status(400).send('Invalid filename');
    }

    const file = path.join(__dirname, 'files', filename);

    res.download(file, filename, (err) => {
        if (err) {
            console.error("Error downloading file:", err);
            res.status(404).send("File not found.");
        }
    });
});

// Start server
app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
    console.log(`- Game Scam: http://localhost:${port}/game`);
    console.log(`- Security Scam: http://localhost:${port}/security`);
    console.log(`- Prize Scam: http://localhost:${port}/prize`);
});
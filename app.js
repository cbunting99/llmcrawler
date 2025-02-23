const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const { Server } = require('socket.io');
const fs = require('fs').promises;

const app = express();
const server = http.createServer(app);
const io = new Server(server);
const port = 3000;

// Queue for managing crawler requests
class RequestQueue {
    constructor() {
        this.queue = [];
        this.isProcessing = false;
    }

    async add(socket, urls, rateLimit, proxyFile) {
        this.queue.push({ socket, urls, rateLimit, proxyFile });
        if (!this.isProcessing) {
            await this.processNext();
        }
    }

    async processNext() {
        if (this.queue.length === 0) {
            this.isProcessing = false;
            return;
        }

        this.isProcessing = true;
        const { socket, urls, rateLimit, proxyFile } = this.queue[0];

        try {
            await processUrls(socket, urls, rateLimit, proxyFile);
        } catch (error) {
            console.error('Error processing URLs:', error);
            socket.emit('crawlError', {
                message: 'Internal server error',
                type: 'error'
            });
        }

        this.queue.shift();
        await this.processNext();
    }
}

const requestQueue = new RequestQueue();

// Progress persistence
const PROGRESS_FILE = 'crawler_progress.json';

async function saveProgress(socketId, data) {
    try {
        const progress = {
            timestamp: new Date().toISOString(),
            socketId,
            data
        };
        await fs.writeFile(PROGRESS_FILE, JSON.stringify(progress));
    } catch (error) {
        console.error('Error saving progress:', error);
    }
}

async function loadProgress(socketId) {
    try {
        const data = await fs.readFile(PROGRESS_FILE, 'utf8');
        const progress = JSON.parse(data);
        if (progress.socketId === socketId) {
            return progress.data;
        }
    } catch (error) {
        // No progress file or invalid data
        return null;
    }
}

// URL validation
function validateUrls(urls) {
    const validUrls = [];
    const invalidUrls = [];

    urls.forEach(url => {
        try {
            new URL(url);
            validUrls.push(url);
        } catch {
            invalidUrls.push(url);
        }
    });

    return { validUrls, invalidUrls };
}

// Process URLs with Python script
async function processUrls(socket, urls, rateLimit = 5.0, proxyFile) {
    let args = ['crawl_lyrics.py', '--rate-limit', rateLimit.toString()];
    if (proxyFile) {
        args.push('--proxy-file', proxyFile);
    }
    urls.forEach(url => args.push(url));
    const pythonProcess = spawn('python', args);

    pythonProcess.stdout.on('data', async (data) => {
        try {
            const statusUpdate = JSON.parse(data.toString());
            if (statusUpdate.error_details) {
                socket.emit('crawlError', {
                    message: statusUpdate.error_details,
                    type: 'crawl'
                });
            }
            
            // Save progress
            if (statusUpdate.status === 'update') {
                await saveProgress(socket.id, statusUpdate.data);
            }
            
            socket.emit('statusUpdate', statusUpdate);
        } catch (error) {
            console.error('Error parsing Python output:', error);
        }
    });

    pythonProcess.stderr.on('data', (data) => {
        const errorMsg = data.toString().trim();
        console.error(`Python Error: ${errorMsg}`);
        
        // Parse error message and handle metadata warnings
        const errorType = errorMsg.startsWith('WARNING:') ? 'warning' : 'error';
        const message = errorMsg.replace(/^(ERROR|WARNING): /, '');
        
        socket.emit('crawlError', {
            message,
            type: errorType
        });

        if (message.includes('Missing metadata')) {
            socket.emit('statusUpdate', {
                status: 'metadata_warning',
                message: message
            });
        }
    });

    return new Promise((resolve, reject) => {
        pythonProcess.on('close', (code) => {
            if (code !== 0) {
                socket.emit('crawlError', {
                    message: 'Crawler script failed',
                    type: 'process'
                });
                reject(new Error('Crawler process failed'));
            } else {
                socket.emit('crawlComplete', {
                    message: 'Crawling completed successfully',
                    type: 'success'
                });
                resolve();
            }
        });
    });
}

// Serve static files from 'public' directory
app.use(express.static('public'));
app.use(express.json());

// Serve the main page
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Download route for CSV file
app.get('/download', (req, res) => {
    const file = 'song_lyrics.csv';
    res.download(file, (err) => {
        if (err) {
            res.status(404).send('File not found');
        }
    });
});

// WebSocket connection handling
io.on('connection', async (socket) => {
    console.log('Client connected:', socket.id);

    // Try to restore progress
    const progress = await loadProgress(socket.id);
    if (progress) {
        socket.emit('statusUpdate', {
            status: 'restore',
            data: progress
        });
    }

    socket.on('startCrawling', (data) => {
        const urls = data.urls.split('\n').filter(url => url.trim());
        let rateLimit = parseFloat(data.rateLimit) || 5.0;
        const proxyFile = data.proxyFile;
        
        if (!proxyFile) {
            socket.emit('crawlError', {
                message: 'Proxy List File Path cannot be empty',
                type: 'validation'
            });
            return;
        }

        if (rateLimit < 1.0) {
            socket.emit('crawlError', {
                message: 'Rate limit must be at least 1 second',
                type: 'validation'
            });
            return;
        }

        const { validUrls, invalidUrls } = validateUrls(urls);

        if (invalidUrls.length > 0) {
            socket.emit('crawlError', {
                message: `Invalid URLs detected: ${invalidUrls.join(', ')}`,
                type: 'validation'
            });
            return;
        }

        // Add request to queue
        requestQueue.add(socket, validUrls, rateLimit, proxyFile).catch(error => {
            console.error('Queue processing error:', error);
        });

        // Send initial status
        socket.emit('statusUpdate', { 
            status: 'started', 
            data: { 
                total_urls: validUrls.length,
                urls_crawled: 0,
                errors: 0,
                metadata_missing: 0
            }
        });
    });

    socket.on('disconnect', () => {
        console.log('Client disconnected:', socket.id);
    });
});

server.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
import {TwelveLabs} from 'twelvelabs-js';
import dotenv from 'dotenv';
import {readFileSync} from 'fs';
import OpenAI from 'openai';

const sample = readFileSync('./sample-response.json', 'utf-8');
dotenv.config();

const prompt =
	"Analyze the following Instagram reel from a tech blogger influencer and provide a detailed report in JSON format, including as many details as possible in the following sections: Comprehensive Description (provide a thorough overview of the reel's content, including key themes, narratives, visuals, dialogues, and important details); Categorization (assign appropriate categories or genres such as technology, gadgets, reviews, tutorials, and list relevant subcategories or topics covered, providing detailed reasoning); Timeline of Key Events (outline a detailed chronological timeline of significant events, scenes, or topics discussed, including precise timestamps in seconds and detailed descriptions for each event); Main Ideas and Themes (summarize all central ideas, messages, or arguments presented, highlighting recurring themes or motifs with detailed explanations); Vibe and Mood Analysis (describe the overall vibe or atmosphere in detail, noting any emotional tones or shifts throughout the reel with as much specificity as possible); Music and Audio Elements (identify any music tracks used, including details about genre, mood, artist names, and specific aspects of the music, and comment extensively on how the music contributes to the reel's overall impact). Structure the JSON output with appropriate keys for each section, ensuring the data is well-organized and machine-readable. Do not include any formatting or markdown, remove any new line characters from the JSON output to make it a single line, and ensure the JSON is valid.";

const gptPrompToFormat = `You are a JSON formatter. Your task is to transform a given JSON into a structured format while keeping all content intact. Use the following target structure as a guide. Ensure that key names and casing remain exactly as in the target format, fitting the provided content into the appropriate keys. Target JSON Structure: { "ComprehensiveDescription": { "overview": "", "keyThemes": [], "narratives": [], "visuals": [], "dialogues": [ { "timestamp": "", "text": "" } ], "importantDetails": [] }, "Categorization": { "primaryCategory": "", "subCategories": [], "detailedReasoning": "" }, "TimelineOfKeyEvents": [ { "timestamp": "", "description": "" } ], "MainIdeasAndThemes": { "centralIdeas": [], "recurringThemes": [ { "theme": "", "explanation": "" } ] }, "VibeAndMoodAnalysis": { "overallVibe": "", "emotionalTones": [ { "timeframe": "", "tone": "" } ] }, "MusicAndAudioElements": { "musicTracks": "", "details": "", "contributionToImpact": "" } }. `;

const generateText = async () => {
	const client = new TwelveLabs({apiKey: process.env.TWELVE_LABS_API_KEY});
	const openai = new OpenAI();
	// const res = await client.generate.text(
	// 	'6743b78e60acab831b3c8db5',
	// 	prompt,
	// 	0.8,
	// 	{}
	// );

	const cleanedData = sample.replace(/\n/g, '').replace(/\+/g, '');
	const completion = await openai.chat.completions.create({
		model: 'gpt-4o',
		messages: [{role: 'user', content: gptPrompToFormat + cleanedData}]
	});

	console.log(completion.choices[0].message.content);
};

generateText();

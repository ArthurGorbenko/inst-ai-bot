import { TwelveLabs } from "twelvelabs-js";
import dotenv from "dotenv";
import { readFileSync } from "fs";
import { MongoClient } from "mongodb";
import OpenAI from "openai";
import fixJSONPrompt from "./prompts/1.fix-json.js";

dotenv.config();

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const uri = "mongodb://localhost:27017/creator-kb";

const connectToMongo = async () => {
  console.log("Connecting to MongoDB...");
  const client = new MongoClient(uri);
  await client.connect();
  console.log("Connected to MongoDB");
  const db = client.db("creator-kb");
  return db.collection("raw");
};

const readPrompts = () => {
  console.log("Reading prompts...");
  const prompts = [
    readFileSync("./prompts/1.comprehensive_description.txt", "utf-8"),
    readFileSync("./prompts/1.categorization.txt", "utf-8"),
    readFileSync("./prompts/1.timeline.txt", "utf-8"),
    readFileSync("./prompts/1.main-ideas.txt", "utf-8"),
    readFileSync("./prompts/1.vibe-music.txt", "utf-8"),
    readFileSync("./prompts/1.music-audio.txt", "utf-8"),
  ];
  console.log("Prompts read successfully");
  return prompts;
};

const cleanData = (data) => {
  console.log("Cleaning data...");
  const cleanedData = data
    .replace(/\n/g, "")
    .replace(/\+/g, "")
    .replace(/`/g, "'");
  console.log("Data cleaned");
  return cleanedData;
};

const updateCollection = async (collection, mediaId, data) => {
  const cleanedData = cleanData(data);
  try {
    console.log(`Parsing data for mediaId: ${mediaId}`);
    const parsedData = JSON.parse(cleanedData);
    console.log("Data parsed successfully");

    // Add timestamps
    const timestamp = new Date();
    await collection.findOneAndUpdate(
      { mediaId },
      {
        $set: {
          ...parsedData,
          updatedAt: timestamp,
        },
        $setOnInsert: {
          createdAt: timestamp,
        },
      },
      { upsert: true }
    );

    console.log(`Collection updated for mediaId: ${mediaId}`);
    return parsedData;
  } catch (error) {
    if (error instanceof SyntaxError && error.message.includes("JSON")) {
      console.log("JSON parse error detected, attempting to fix JSON...");
      const fixedJSONPrompt = fixJSONPrompt(cleanedData);
      const response = await openai.chat.completions.create({
        model: "gpt-4o-mini",
        messages: [{ role: "user", content: fixedJSONPrompt }],
        temperature: 0,
        response_format: { type: "json_object" },
      });

      console.log("OPENAI response", response);

      const fixedJson = response.choices[0].message.content;
      const parsedFixedJson = JSON.parse(fixedJson);

      await collection.findOneAndUpdate(
        { mediaId },
        { $set: { ...parsedFixedJson } },
        { upsert: true }
      );

      console.log(`Collection updated with fixed JSON for mediaId: ${mediaId}`);
      return parsedFixedJson;
    } else {
      console.error("Error updating collection:", error);
      throw error; // Re-throw the error if it's not a JSON parse error
    }
  }
};

const generateText = async () => {
  try {
    const collection = await connectToMongo();
    const client = new TwelveLabs({ apiKey: process.env.TWELVE_LABS_API_KEY });
    const prompts = readPrompts();
    const videos = await client.index.video.list("6743b77b12e44d1c53a44ab5");
    const videoIDs = videos.map((video) => video.id);

    const videosMongo = await collection.find({}, { mediaId: 1 }).toArray();
    const existingIDsMongo = videosMongo.map((v) => v.mediaId);

    console.log(`Processing ${videoIDs.length} videos...`);

    for (const currVideoID of videoIDs) {
      console.log(`Checking video ID: ${currVideoID}`);
      if (existingIDsMongo.includes(currVideoID)) {
        console.log(
          `Video ${currVideoID} already exists in MongoDB, skipping...`
        );
        continue;
      }
      console.log(
        `Processing ${prompts.length} prompts for video ${currVideoID}`
      );
      for (const prompt of prompts) {
        console.log(
          `Generating text for videoID: ${currVideoID} with prompt: ${prompt}`
        );
        const res = await client.generate.text(currVideoID, prompt, 0.8, {});
        console.log(`Text generation completed for video ${currVideoID}`);
        console.log(`Updating MongoDB collection with generated text...`);
        await updateCollection(collection, currVideoID, res.data);
        console.log(
          `MongoDB collection updated successfully for video ${currVideoID}`
        );
      }
      console.log(`Completed processing all prompts for video ${currVideoID}`);
    }
    console.log(`Finished processing all videos`);
  } catch (error) {
    console.error("Error generating text:", error);
  }
};

generateText();

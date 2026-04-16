const YTMusic = require('ytmusic-api').default;
const ytmusic = new YTMusic();

async function main() {
    // 1. Parse your existing JSON secret
    const oauthData = JSON.parse(process.env.YTM_OAUTH_JSON);

    try {
        // 2. The JS library uses 'initialize' to set up the session
        // If your JSON has the correct 'cookie' field inside, it uses it.
        await ytmusic.initialize(oauthData.cookie || ""); 

        const playlistId = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur";
        const playlist = await ytmusic.getPlaylist(playlistId);
        
        console.log(`Successfully accessed: ${playlist.name}`);
    } catch (error) {
        console.error("Access Denied. Error:", error.message);
    }
}
main();

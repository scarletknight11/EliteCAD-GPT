<?php

session_start();
if (!isset($_SESSION['email'])) {
    header("Location: index.php");
    exit();
}

?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Page</title>
    <link rel="stylesheet" href="styles.css">
</head>
<header class="chat-header">
        <div class="header-content">
            <h1><i class="fas fa-robot"></i> Elite CAD AI Assistant</h1>
            <div class="user-info">
                <span>Welcome, <?=htmlspecialchars($_SESSION['name'])?></span>
                <a href="logout.php" class="logout-btn">
                    <i class="fas fa-sign-out-alt"></i> Logout
                </a>
            </div>
        </div>
    </header>
    <main class="chat-container">
        <!-- Streamlit iframe -->
        <iframe src="http://your-streamlit-app-url" class="chatbot-iframe"></iframe>
    </main>
    <footer class="chat-footer">
        <p>© <?=date('2025')?> Elite CAD Designs. All rights reserved.</p>
    </footer>
</body>

</body>
</html>

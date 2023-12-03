function showMessage(message) {
    const messageContainer = document.getElementById('messageContainer');
    messageContainer.textContent = message;
    messageContainer.style.display = 'block';

    // Remove the message after a delay and fade it out
    setTimeout(() => {
        messageContainer.classList.add('fade-out');

        // Hide and reset the message container after the fade-out
        setTimeout(() => {
            messageContainer.style.display = 'none';
            messageContainer.classList.remove('fade-out');
        }, 6000); // This should match the duration of the opacity transition in CSS
    }, 6000); // Adjust this for how long you want the message to be visible
}

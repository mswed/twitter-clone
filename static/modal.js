// Get the button that opens the modal
const newMessageBtn = document.getElementById('create-message');

newMessageBtn.addEventListener('click', async (e) => {
    e.preventDefault()
    const form = document.getElementById("new-message-form");
    let formData = new FormData(form);
    const res = await axios.post(`/messages/new`, formData);
    // We check if we got redirected to anywhere other than the homepage
    if (res.request.responseURL != '/') {
        await flash('Created a new Warbler!', 'success')
        const modal = document.getElementById('messageModal');
        const theModal = bootstrap.Modal.getOrCreateInstance(modal);
        theModal.hide();
        document.querySelector("div.modal-backdrop").remove()

    }
})

async function flash(message, category) {
    // We get the flash messages div
    const container = document.querySelector('div.container');

    // We create a div
    const m = document.createElement('div');
    m.className = (`alert alert-${category}`);
    m.innerText = message;

    container.prepend(m)
}
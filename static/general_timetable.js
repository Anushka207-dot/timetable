
const classSelect = document.getElementById("class");
const sectionSelect = document.getElementById("section");
const viewButton = document.getElementById("viewTimetableBtn");
const selectedClass = document.getElementById("selectedClass");
const timetableBody = document.getElementById("timetableBody");

viewButton.addEventListener("click", function () {

    const selectedClassValue = classSelect.value;
    const selectedSectionValue = sectionSelect.value;

    if (!selectedClassValue || !selectedSectionValue) {
        alert("Please select both class and section.");
        return;
    }

    selectedClass.textContent =
        "Class " + selectedClassValue +
        " - Section " + selectedSectionValue;

    timetableBody.innerHTML = `
        <tr>
            <td colspan="9" class="empty-message">
                No timetable is available for this class yet.
                Please generate the timetable first.
            </td>
        </tr>
    `;
});

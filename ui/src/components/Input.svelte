<script>
    export let type = "text";
    export let placeholder = "placeholder";
    export let value = "";
    export let min="";
    export let max="";
    export let step="";

</script>

<div class="text-left">
    <p class="text-black w-full">
        <slot />
    </p>
    <input
        class="text-black border-black border-1 rounded-lg p-2 w-full my-2"
        {type}
        {min}
        {max}
        {step}
        bind:value={value}
        {placeholder}
    />
</div>
